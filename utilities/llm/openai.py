import os
from langchain_openai import ChatOpenAI

from utilities.llm.modelbase import ModelBase



class OpenAITool(ModelBase):
    """Class for the OpenAI tool."""

    def _get_model(self, **kwargs):
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        # check if the keyargs have tools array
        if "tools" in kwargs:
            tools = kwargs["tools"]
            return ChatOpenAI(model=self.tool_name, openai_api_key=os.environ["OPENAI_API_KEY"]).bind_tools(tools)
        return ChatOpenAI(model=self.tool_name, openai_api_key=os.environ["OPENAI_API_KEY"])
    

    def use(self, prompt: str = "Hello, world!") -> str:
        return self.model.invoke(prompt)

