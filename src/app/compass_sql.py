"""Databricks SQL warehouse access via Statement Execution API (app identity)."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem

SCHEMA_NAME = "ai_compass"
USER_MSG_STRUCTURED = "{}"

_TERMINAL = frozenset({"SUCCEEDED", "FAILED", "CANCELED", "CLOSED"})


def _state_name(state: Any) -> str:
    if state is None:
        return ""
    if hasattr(state, "name"):
        return str(state.name)
    if hasattr(state, "value"):
        return str(state.value)
    return str(state)


def default_assistant_structured_output() -> str:
    return json.dumps(
        {"usecase_name": os.getenv("COMPASS_USECASE_NAME", "")},
        ensure_ascii=False,
    )


def persist_configured() -> bool:
    return bool(sql_warehouse_id() and uc_catalog())


def sql_warehouse_id() -> str:
    return (
        os.getenv("COMPASS_SQL_WAREHOUSE_ID", "").strip()
        or os.getenv("DATABRICKS_SQL_WAREHOUSE_ID", "").strip()
    )


def uc_catalog() -> str:
    return os.getenv("COMPASS_UC_CATALOG", "").strip()


def _now_sql() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _params(**kwargs: str) -> list[StatementParameterListItem]:
    return [StatementParameterListItem(name=k, value=v) for k, v in kwargs.items()]


def _poll_until_terminal(w: WorkspaceClient, resp: Any) -> Any:
    stmt_id = resp.statement_id
    while True:
        name = _state_name(resp.status.state) if resp.status else ""
        if name in _TERMINAL:
            return resp
        time.sleep(0.25)
        resp = w.statement_execution.get_statement(stmt_id)


def run_statement(
    w: WorkspaceClient,
    statement: str,
    *,
    parameters: Optional[list[StatementParameterListItem]] = None,
    wait_timeout: str = "50s",
) -> Any:
    catalog = uc_catalog()
    resp = w.statement_execution.execute_statement(
        warehouse_id=sql_warehouse_id(),
        catalog=catalog,
        schema=SCHEMA_NAME,
        statement=statement,
        parameters=parameters or [],
        wait_timeout=wait_timeout,
    )
    resp = _poll_until_terminal(w, resp)
    state = _state_name(resp.status.state) if resp.status else ""
    if state == "FAILED":
        err = resp.status.error if resp.status else None
        msg = getattr(err, "message", None) or str(err or "SQL failed")
        raise RuntimeError(msg)
    return resp


def fetch_all(
    w: WorkspaceClient,
    statement: str,
    *,
    parameters: Optional[list[StatementParameterListItem]] = None,
) -> list[list[Any]]:
    resp = run_statement(w, statement, parameters=parameters)
    if not resp.result or not resp.result.data_array:
        return []
    return resp.result.data_array


def create_conversation(
    w: WorkspaceClient,
    conversation_id: str,
    user_email: str,
) -> None:
    ts = _now_sql()
    run_statement(
        w,
        """
        INSERT INTO conversations (conversation_id, user_email, created_at, updated_at)
        VALUES (:conversation_id, :user_email, :created_at, :updated_at)
        """,
        parameters=_params(
            conversation_id=conversation_id,
            user_email=user_email,
            created_at=ts,
            updated_at=ts,
        ),
    )


def touch_conversation(w: WorkspaceClient, conversation_id: str, user_email: str) -> None:
    run_statement(
        w,
        """
        UPDATE conversations
        SET updated_at = :updated_at
        WHERE conversation_id = :conversation_id AND user_email = :user_email
        """,
        parameters=_params(
            updated_at=_now_sql(),
            conversation_id=conversation_id,
            user_email=user_email,
        ),
    )


def next_message_sequence(
    w: WorkspaceClient, conversation_id: str, user_email: str
) -> int:
    rows = fetch_all(
        w,
        """
        SELECT COALESCE(MAX(sequence), 0) + 1 AS n
        FROM messages
        WHERE conversation_id = :conversation_id AND user_email = :user_email
        """,
        parameters=_params(conversation_id=conversation_id, user_email=user_email),
    )
    if not rows or rows[0][0] is None:
        return 1
    return int(rows[0][0])


def insert_message(
    w: WorkspaceClient,
    *,
    message_id: str,
    conversation_id: str,
    user_email: str,
    role: str,
    content: str,
    sequence: int,
    structured_output: str,
) -> None:
    seq_item = StatementParameterListItem(
        name="sequence", value=str(sequence), type="INT"
    )
    base = _params(
        message_id=message_id,
        conversation_id=conversation_id,
        user_email=user_email,
        role=role,
        content=content,
        structured_output=structured_output,
        created_at=_now_sql(),
    )
    run_statement(
        w,
        """
        INSERT INTO messages (
          message_id, conversation_id, user_email, role, content, sequence, structured_output, created_at
        )
        VALUES (
          :message_id, :conversation_id, :user_email, :role, :content, :sequence, :structured_output, :created_at
        )
        """,
        parameters=base + [seq_item],
    )


@dataclass
class ConversationRow:
    conversation_id: str
    updated_at: str


def list_conversations(w: WorkspaceClient, user_email: str) -> list[ConversationRow]:
    rows = fetch_all(
        w,
        """
        SELECT conversation_id, CAST(updated_at AS STRING) AS updated_at
        FROM conversations
        WHERE user_email = :user_email
        ORDER BY updated_at DESC
        LIMIT 200
        """,
        parameters=_params(user_email=user_email),
    )
    out: list[ConversationRow] = []
    for r in rows:
        out.append(ConversationRow(conversation_id=str(r[0]), updated_at=str(r[1])))
    return out


def load_messages(w: WorkspaceClient, conversation_id: str, user_email: str) -> list[dict]:
    rows = fetch_all(
        w,
        """
        SELECT role, content
        FROM messages
        WHERE conversation_id = :conversation_id AND user_email = :user_email
        ORDER BY sequence ASC
        """,
        parameters=_params(conversation_id=conversation_id, user_email=user_email),
    )
    return [{"role": str(r[0]), "content": str(r[1])} for r in rows]


def new_id() -> str:
    return str(uuid.uuid4())
