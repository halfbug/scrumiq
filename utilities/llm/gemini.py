import os
import logging
from typing import Any, Union, AsyncGenerator
from langchain_google_genai import ChatGoogleGenerativeAI
from utilities.llm.modelbase import ModelBase

class GeminiTool(ModelBase):
    """Class for the Gemini tool."""

    def _get_model(self, **kwargs):
        model = ChatGoogleGenerativeAI(
            model=self.tool_name,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            cache=False,
            verbose=True
        )
        tools = kwargs.get("tools", None)
        if tools:
            logging.info(f"Binding tools: {tools}")
            return model.bind_tools(tools)
        return model

    def use(self, prompt: Any = "Hello, world!") -> str:
        # print(f"tool_name: {self.tool_name}") 
        if not self.model:
            tools = self.agent.tools if hasattr(self.agent, 'tools') else None
            self.model = self._get_model(tools=tools)
        # print(f"Using model: {self.model}")
        # print(f"Prompt: {prompt}")
        response = self.model.invoke(prompt)
        # print(f"Response: {response}")
        response.pretty_print()
        response.response_metadata["model_name"] = self.tool_name
        return response

    async def astream(self, prompt: Any) -> AsyncGenerator:
        if not self.model:
            tools = self.agent.tools if hasattr(self.agent, 'tools') else None
            self.model = self._get_model(tools=tools)
        async for chunk in self.model.astream(prompt):
            chunk.pretty_print()
            yield chunk
