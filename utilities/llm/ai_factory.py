# from utilities.llm.gemini import GeminiTool
# from utilities.llm.openai import OpenAITool
# # Remove Hugging Face import
# # from utilities.llm.huggingface import HuggingFaceTool
# from utilities.llm.deepseek import DeepSeekTool

class AIFactory:
    @staticmethod
    def get_tool(tool_name, **kwargs):
        

        # # if tool_name.startswith('gemini'):
        # #     return GeminiTool(tool_name, **kwargs)
        # # elif tool_name.startswith('gpt'):
        # #     return OpenAITool(tool_name, **kwargs)
        # # elif tool_name == 'deepseek-ai/DeepSeek-R1':
        # #     return DeepSeekTool(tool_name)
        # # elif tool_name == 'deepseek-chat':
        # #     return DeepSeekTool(tool_name)
        # else:
            raise ValueError('Invalid AI tool selection')