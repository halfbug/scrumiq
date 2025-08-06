from langchain_core.prompts import PromptTemplate, ChatMessagePromptTemplate
from pydantic import BaseModel
from typing import Any
from utilities.llm.ai_factory import AIFactory
from core.model_config import get_active_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

def run_chain(
    prompt_template: str,
    model_name: str,
    **kwargs
) -> Any:
    """
    General function to run a prompt with a model using AIFactory and return the result.
    Args:
        prompt_template: The prompt template string.
        model_name: The model name for AIFactory.
        **kwargs: Variables for the prompt.
    Returns:
        Result from the model.
    """
    try:
        # Use PromptTemplate instead of ChatMessagePromptTemplate to avoid role validation error
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=list(kwargs.keys()),
        )
        print(prompt.invoke(kwargs))
        active_model = get_active_model(model_name) or model_name
        model = AIFactory.get_tool(active_model)
        # Remove the chain (|) operator, directly use model.use with the prompt
        prompt_str = prompt.invoke(kwargs)
        result = model.use(prompt_str)
        print(f"result----------", result)
        
        if isinstance(result, AIMessage):
            result = result.content
        return result
    except Exception as e:
        print(f"Error in run_chain: {e}")
        return {"error": str(e)}

# Example usage:
# if __name__ == "__main__":
#     PROMPT = "Answer the user query: {query}"
#     result = run_chain(PROMPT, "gemini-2.5-flash", query="Tell me a joke.")
#     print(result)