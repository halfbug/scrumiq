import os
from langchain_deepseek import ChatDeepSeek
from utilities.llm.modelbase import ModelBase

class DeepSeekTool(ModelBase):
    """Class for DeepSeek API integration."""

    def _get_model(self):
        if "DEEPSEEK_API_KEY" not in os.environ:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")
        return ChatDeepSeek(
            model=self.tool_name,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
           )

    def use(self, prompt: str) -> str:
        return self.model.invoke(prompt)
