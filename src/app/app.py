import os

import pypdf
import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

import compass_sql as cs

NONE_SENTINEL = "__compass_none__"


@st.cache_resource
def _workspace_client():
    """One client per Streamlit server process; uses Databricks unified auth."""
    return WorkspaceClient()


def _get_workspace():
    try:
        return _workspace_client()
    except (ValueError, OSError) as e:
        st.error(
            "**Databricks authentication is not configured** (model endpoint and SQL need this).\n\n"
            "For **local** runs, set environment variables before `streamlit run`:\n"
            "- `DATABRICKS_HOST` — e.g. `https://adb-xxxx.1.azuredatabricks.net`\n"
            "- `DATABRICKS_TOKEN` — a personal access token for that workspace\n\n"
            "Alternatively use `~/.databrickscfg` and set `DATABRICKS_CONFIG_PROFILE`.\n\n"
            "Docs: https://docs.databricks.com/en/dev-tools/auth.html#databricks-client-unified-authentication\n\n"
            f"SDK message: `{e}`"
        )
        st.stop()


def _resolve_user_email() -> str:
    headers = st.context.headers
    email = (
        headers.get("X-Forwarded-Email")
        or headers.get("x-forwarded-email")
        or headers.get("X-Forwarded-Preferred-Username")
        or headers.get("x-forwarded-preferred-username")
        or headers.get("X-Forwarded-User")
        or headers.get("x-forwarded-user")
        or ""
    ).strip()
    return email.lower()


def _build_chat_history():
    history = []
    for msg in st.session_state.messages:
        role = (
            ChatMessageRole.USER
            if msg["role"] == "user"
            else ChatMessageRole.ASSISTANT
        )
        history.append(ChatMessage(role=role, content=msg["content"]))
    return history


if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_pdf_text" not in st.session_state:
    st.session_state.active_pdf_text = ""
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "show_pdf_prompt" not in st.session_state:
    st.session_state.show_pdf_prompt = False
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "is_logged_out" not in st.session_state:
    st.session_state.is_logged_out = False

USER_EMAIL = _resolve_user_email()
if not USER_EMAIL:
    st.error(
        "Could not read your identity from Databricks Apps SSO headers. "
        "Open this app from Databricks Apps and verify app authentication is enabled."
    )
    st.stop()

w = _get_workspace()

st.title("AI Compass")
header_left, header_right = st.columns([8, 2])
with header_left:
    st.caption(f"Signed in as {USER_EMAIL}")
with header_right:
    st.caption(f"Profile: {USER_EMAIL}")
    if st.session_state.is_logged_out:
        if st.button("Login", use_container_width=True):
            st.session_state.is_logged_out = False
            st.rerun()
    else:
        if st.button("Logout", use_container_width=True):
            st.session_state.is_logged_out = True
            st.session_state.messages = []
            st.session_state.current_conversation_id = None
            st.session_state.active_pdf_text = ""
            st.rerun()

if st.session_state.is_logged_out:
    st.info("You are logged out from this app session. Click Login to continue.")
    st.stop()

st.markdown(
    """
<style>
    [data-testid="stFileUploader"] small {
        display: none;
    }
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    if st.button("New chat"):
        st.session_state.messages = []
        st.session_state.current_conversation_id = None
        st.session_state.active_pdf_text = ""
        st.session_state.compass_pick = NONE_SENTINEL
        st.session_state.compass_prev_pick = NONE_SENTINEL
        st.rerun()

    if cs.persist_configured():
        try:
            conv_rows = cs.list_conversations(w, USER_EMAIL)
        except Exception as err:
            st.error(f"Could not load conversations: {err}")
            conv_rows = []
        ids = [r.conversation_id for r in conv_rows]
        labels = {
            r.conversation_id: f"{r.updated_at[:19]} · {r.conversation_id[:8]}"
            for r in conv_rows
        }
        cid_cur = st.session_state.current_conversation_id
        if cid_cur and cid_cur not in ids:
            ids = [cid_cur] + ids
            labels[cid_cur] = f"(this session) · {cid_cur[:8]}"

        opts = [NONE_SENTINEL] + ids

        def _fmt(oid):
            if oid == NONE_SENTINEL:
                return "— Current / new —"
            return labels.get(oid, f"{oid[:8]}…")

        idx = 0
        if cid_cur and cid_cur in ids:
            idx = ids.index(cid_cur) + 1

        st.radio(
            "Past chats",
            opts,
            index=idx,
            format_func=_fmt,
            key="compass_pick",
            label_visibility="visible",
        )

        if "compass_prev_pick" not in st.session_state:
            st.session_state.compass_prev_pick = st.session_state.compass_pick
        elif st.session_state.compass_pick != st.session_state.compass_prev_pick:
            pick = st.session_state.compass_pick
            if pick == NONE_SENTINEL:
                st.session_state.messages = []
                st.session_state.current_conversation_id = None
            else:
                try:
                    st.session_state.messages = cs.load_messages(
                        w, pick, USER_EMAIL
                    )
                except Exception as err:
                    st.error(f"Could not load chat: {err}")
                    st.session_state.messages = []
                st.session_state.current_conversation_id = pick
            st.session_state.active_pdf_text = ""
            st.session_state.compass_prev_pick = pick
            st.rerun()
    else:
        st.caption(
            "Persistence off: set COMPASS_UC_CATALOG and "
            "COMPASS_SQL_WAREHOUSE_ID (or DATABRICKS_SQL_WAREHOUSE_ID)."
        )

    uploaded_file = st.file_uploader("Attach PDF", type="pdf")
    if uploaded_file:
        if st.session_state.uploaded_file != uploaded_file:
            st.session_state.show_pdf_prompt = True
        st.session_state.uploaded_file = uploaded_file
        st.success(f"Attached: {uploaded_file.name}")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.session_state.show_pdf_prompt and st.session_state.uploaded_file:
    st.info(
        f"PDF {st.session_state.uploaded_file.name} attached — ask a question about it."
    )

prompt = st.chat_input("Ask something...")

if prompt:
    st.session_state.show_pdf_prompt = False
    display_text = prompt

    if st.session_state.uploaded_file:
        with st.spinner("Processing document..."):
            pdf = pypdf.PdfReader(st.session_state.uploaded_file)
            pdf_text = ""
            for page in pdf.pages:
                pdf_text += page.extract_text() + "\n"

            st.session_state.active_pdf_text = pdf_text
            display_text = f"**Attached: {st.session_state.uploaded_file.name}**\n\n{prompt}"

    st.session_state.messages.append({"role": "user", "content": display_text})

    with st.chat_message("user"):
        st.markdown(display_text)

    with st.chat_message("assistant"):
        agent_name = os.getenv("SERVING_ENDPOINT_NAME", "compass_v_1")
        with st.spinner("Thinking..."):
            try:
                if st.session_state.active_pdf_text:
                    context_payload = (
                        f"DOCUMENT ATTACHED:\n"
                        f"{st.session_state.active_pdf_text}\n\n"
                        f"User Question: {prompt}"
                    )
                else:
                    context_payload = prompt

                if cs.persist_configured():
                    conv_id = st.session_state.current_conversation_id
                    if not conv_id:
                        conv_id = cs.new_id()
                        st.session_state.current_conversation_id = conv_id
                        cs.create_conversation(w, conv_id, USER_EMAIL)
                    seq_u = cs.next_message_sequence(w, conv_id, USER_EMAIL)
                    cs.insert_message(
                        w,
                        message_id=cs.new_id(),
                        conversation_id=conv_id,
                        user_email=USER_EMAIL,
                        role="user",
                        content=display_text,
                        sequence=seq_u,
                        structured_output=cs.USER_MSG_STRUCTURED,
                    )
                    cs.touch_conversation(w, conv_id, USER_EMAIL)

                chat_history = _build_chat_history()
                chat_history[-1] = ChatMessage(
                    role=ChatMessageRole.USER,
                    content=context_payload,
                )

                db_resp = w.serving_endpoints.query(
                    name=agent_name,
                    messages=chat_history,
                )

                response_text = db_resp.choices[0].message.content
                st.markdown(response_text)

                st.session_state.messages.append(
                    {"role": "assistant", "content": response_text}
                )

                if cs.persist_configured():
                    conv_id = st.session_state.current_conversation_id
                    seq_a = cs.next_message_sequence(w, conv_id, USER_EMAIL)
                    cs.insert_message(
                        w,
                        message_id=cs.new_id(),
                        conversation_id=conv_id,
                        user_email=USER_EMAIL,
                        role="assistant",
                        content=response_text,
                        sequence=seq_a,
                        structured_output=cs.default_assistant_structured_output(),
                    )
                    cs.touch_conversation(w, conv_id, USER_EMAIL)
                    if conv_id and "compass_pick" in st.session_state:
                        st.session_state.compass_pick = conv_id
                        st.session_state.compass_prev_pick = conv_id

            except Exception as e:
                st.error(f"Error: {e}")
