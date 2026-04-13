from databricks_openai import DatabricksOpenAI
from prompts import SYSTEM_PROMPT
import mlflow
from typing import Any, List
from mlflow.pyfunc import ChatModel
from mlflow.types.llm import (
    ChatMessage,
    ChatParams,
    ChatCompletionResponse,
    ChatChoice,
)

class AICompass(ChatModel):
    def __init__(self, model_name: str = "databricks-claude-sonnet-4-5"):
        super().__init__()
        self.model_name = model_name
        self.system_prompt = SYSTEM_PROMPT
        # self.client = DatabricksOpenAI()

    def load_context(self, context):
        self.client = DatabricksOpenAI()

    def predict(
        self,
        context: Any,
        messages: List[ChatMessage],
        params: ChatParams = None,
    ) -> ChatCompletionResponse:

        msgs_payload = [{"role": m.role, "content": m.content} for m in messages]
        msgs_payload = [{"role": "system", "content": self.system_prompt}] + msgs_payload

        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=msgs_payload,
        )
        text = resp.choices[0].message.content.strip()
        choice = ChatChoice(
            index=0,
            message=ChatMessage(role="assistant", content=text),
            finish_reason="stop",
        )
        return ChatCompletionResponse(choices=[choice])
    
agent = AICompass()
mlflow.models.set_model(agent)