# utilities/llm/huggingface.py
import os
from langchain_huggingface import HuggingFaceEndpoint
from utilities.llm.modelbase import ModelBase
from langchain_core.messages import AIMessage

class HuggingFaceTool(ModelBase):
    """Class for Hugging Face Hub models (Inference API)"""
    
    def _get_model(self):
        if "HUGGINGFACEHUB_API_TOKEN" not in os.environ:
            raise ValueError("HUGGINGFACEHUB_API_TOKEN environment variable not set")
        
        return HuggingFaceEndpoint(
            repo_id=self.tool_name,
            task="text-generation",  # Ensure the task is specified correctly
            max_length=128,
            temperature=0.5,
            huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"]
        ) 

    def use(self, prompt: str) -> str:
        response = self.model.invoke(prompt)
        print("prompt", prompt)
        print("response", type(response), response)
        
        if isinstance(response, str):
            token_usage_details = {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0
            }
            message = AIMessage(content=response, response_metadata={"token_usage":token_usage_details, "model_name":self.tool_name})
            print("message", message)   
            return message
        
        return response