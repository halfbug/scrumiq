import re
import json
# import json5
from typing import Dict, Any, List
from langchain_core.messages import AIMessage

# def convert_to_clean_json(raw_content: str) -> Dict[str, Any]:
#     """
#     Converts raw JSON content into a clean JSON format.
#     Handles cases where the content is embedded in markdown, text, or raw JSON.

#     Parameters:
#         raw_content (str): Raw JSON content.

#     Returns:
#         dict: Cleaned dictionary matching the expected schema.
#     """
#     content = raw_content.strip()
#     parsed_content = None

#     # 1. Try to extract from code blocks first
#     json_block_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
#     if json_block_match:
#         try:
#             parsed_content = json.loads(json_block_match.group(1).strip())
#         except (json.JSONDecodeError, AttributeError):
#             pass

#     # 2. If not in code block, try to find JSON in text content
#     if parsed_content is None:
#         # Look for JSON-like structure in text
#         start_idx = content.find('{')
#         end_idx = content.rfind('}')
#         if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
#             try:
#                 potential_json = content[start_idx:end_idx+1]
#                 parsed_content = json.loads(potential_json)
#             except json.JSONDecodeError:
#                 pass

#     # 3. Try parsing entire content as last resort
#     if parsed_content is None:
#         try:
#             parsed_content = json.loads(content)
#         except json.JSONDecodeError:
#             pass

#     # Create default structure with empty values
#     default_structure = {
#         "question_text": "",
#         "choices": [],
#         "answer": [],
#         "suggested_answer": "",
#         "pairs": [],
#         "groups": [],
#         "terms": [],
#     }

#     # If we successfully parsed something, merge with defaults
#     if parsed_content:
#         return {
#             **default_structure,
#             **{k: v for k, v in parsed_content.items() if k in default_structure}
#         }
    
#     return default_structure
# # print(":::::raw_content",raw_content)
    # # Check if the content contains the code block marker
    # if "```json" in raw_content:
    #     # Use a regular expression to extract the JSON content inside the code block
    #     match = re.search(r"```json\s*(\{.*?\})\s*```", raw_content, re.DOTALL)
    #     if not match:
    #         raise ValueError(f"Invalid JSON content inside code block: {raw_content}")
    #         print(f"Invalid JSON content inside code block: {raw_content}")
    #         return {}   
        
    #     # Extract the matched JSON string
    #     json_content = match.group(1)
    # elif "{" in raw_content and "}" in raw_content:
    #     # Use a regular expression to extract the JSON content inside curly brackets
    #     match = re.search(r"(\{.*?\})", raw_content, re.DOTALL)
    #     if not match:
    #         raise ValueError(f"Invalid JSON content inside curly brackets: {raw_content}")
    #         print(f"Invalid JSON content inside curly brackets: {raw_content}")
    #         return {}
        
    #     # Extract the matched JSON string
    #     json_content = match.group(1)
    # else:
    #     # Assume the raw_content is directly a JSON string
    #     json_content = raw_content

    # # Replace escape characters like \'
    # json_content = json_content.replace("\\'", "'")

    # # Parse the JSON string into a Python dictionary
    # try:
    #     parsed_content = json5.loads(json_content)
    # except json.JSONDecodeError as e:
    #     print(f"Invalid JSON content Decoder Error: {json_content}")
    #     raise ValueError(f"Invalid JSON content Decoder Error: {json_content}") 
    #     return {}

    # # Validate and return the parsed content
    # if not isinstance(parsed_content, dict):
    #     print(f"Parsed content is not a valid JSON object: {parsed_content}")
    #     return {}

def extract_token_usage_details(messages: list, num_messages: int = 1) -> List[Dict[str, Any]]:
    """
    Extracts token usage details from the last `num_messages` messages in the question response.

    Parameters:
        messages (list): List of messages, typically the last `num_messages` messages from the question response.
        num_messages (int): Number of last messages to pick. Defaults to 2.

    Returns:
        list: List of dictionaries containing total tokens, input tokens, output tokens, and model name for each message.
    """
    if len(messages) < num_messages:
        raise ValueError(f"At least {num_messages} messages are required to extract token usage details.")

    selected_messages = messages[-num_messages:]
    token_usage_details_list = []

    for message in selected_messages:
        if isinstance(message, AIMessage):
            usage_metadata = message.response_metadata.get('token_usage', message.usage_metadata)
            token_usage_details = {
                "total_tokens": usage_metadata.get('total_tokens', 0),
                "input_tokens": usage_metadata.get('prompt_tokens', usage_metadata.get('input_tokens', 0)),
                "output_tokens": usage_metadata.get('completion_tokens', usage_metadata.get('output_tokens', 0)),
                "model_name": message.response_metadata.get('model_name', 'gemini_1_5_flash'),
                "message_id": message.id,
                "type": "tool_call" if message.tool_calls else "response"
            }
            token_usage_details_list.append(token_usage_details)

    return token_usage_details_list

def get_message_token_usage(message: AIMessage) -> Dict[str, Any] | None:
    """
    Extracts token usage details from a single message.

    Parameters:
        message (AIMessage): The message to extract token usage from.

    Returns:
        dict: Dictionary containing total tokens, input tokens, output tokens, and model name.
    """
    print(":::::message", message)
    if not isinstance(message, AIMessage):
        return None

    usage_metadata = message.response_metadata.get('token_usage', message.usage_metadata)
    print(":::::usage_metadata", usage_metadata)
    return {
        "total_tokens": usage_metadata.get('total_tokens', 0),
        "input_tokens": usage_metadata.get('prompt_tokens', usage_metadata.get('input_tokens', 0)),
        "output_tokens": usage_metadata.get('completion_tokens', usage_metadata.get('output_tokens', 0)),
        "model_name": message.response_metadata.get('model_name', 'gemini_1_5_flash'),
        "message_id": message.id,
        "type": "tool_call" if message.tool_calls else "response"
    }
