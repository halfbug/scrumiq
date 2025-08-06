import json
import os
import random
from typing import Any, AsyncGenerator, List, Literal, Optional, Tuple, Union
import uuid
from langchain_core.prompts import PromptTemplate
from fastapi import APIRouter, HTTPException, Request, Response, Depends, Header
from fastapi.responses import StreamingResponse

from pydantic import BaseModel

from core.initialize import set_environment_variables
from utilities.helper import convert_to_clean_json, extract_token_usage_details
from utilities.llm.rag_agent import RAGAgent
from utilities.llm.questions_prompt import generate_question_prompt
from utilities.textloader import load_documents_from_folder
from utilities.vectorstore import PineconeVectorStoreHandler
from utilities.llm.difficulty_agent import DifficultyAgent
from utilities.content_filter import filter_images, restore_images
from core.model_config import get_active_model

router = APIRouter()

# set_environment_variables()
# Update model mapping to use lowercase keys
ai_models = { 
    "obsidianai": "gpt-4o-mini",
    "obsidianai": "gpt-4o-mini",
    "azureai": "gemini-2.5-pro-preview-05-06",
    "crimsonai": "deepseek-chat"
}

class QuestionRequest(BaseModel):
    thread_id: str | None = None
    topicTitle: str | None = None
    classGrade: Union[str, int, None] = "9th"
    difficultyLevel: Optional[Literal['Easy', 'Medium', 'Hard']] = 'Medium'
    additionalInfo: str | None = None
    aiTool: Literal['gemini-1.5-flash', 'gpt-4o-mini', 'deepseek-ai/DeepSeek-R1', 'deepseek-chat', 'ObsidianAI', 'AzureAI', 'CrimsonAI'] = 'gemini-1.5-flash'
    customPrompt: str | None = None
    questionType: str | None = None
    user_id: str
    publication_id: str | None = None  # Renamed from publish_id

# Define a model for a question
class Question(BaseModel):
    question_text: Any
    choices: Optional[List[Any]] = None  # Optional: Some questions might not have choices
    answer: Optional[Any] = None 
    suggested_answer: Optional[Any] = None
    pairs: Optional[Any] = None
    groups: Optional[Any] = None
    terms: Optional[Any] = None
    model_name: str  # Add model name field
    

# Define the response model
class QuestionResponse(BaseModel):
    question: Optional[Question] = None  # Changed from questions array to single question
    question_type: str | None = None
    thread_id: str
    message: str | None = None
    checkpoint_id: str | None = None
    parent_checkpointer_id: str | None = None

async def validate_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Access denied: Missing required credentials.")
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Access denied: Invalid credentials provided.")
    return x_api_key

# Update the route decorators to include the dependency
@router.post("/genquestion", name="generate_question", response_model=QuestionResponse, dependencies=[Depends(validate_api_key)])
async def generate_question(request_data: QuestionRequest):
        """
        Generate a question based on the given prompt and language model.

        Args:
            request (Request): The incoming request.
            question (QuestionRequest): The request body containing the prompt and language model.

        Returns:
            Response[GeneratedQuestion]: The response containing the generated question.
        """
        print("request_data", request_data)
        # print("",request_data)
        messageBot=""
        prompt = generate_question_prompt(
        question_type=request_data.questionType,
        topic_title=request_data.topicTitle,
        class_grade=request_data.classGrade,
        difficulty_level=request_data.difficultyLevel,
        additional_info=request_data.additionalInfo,
        
    )if request_data.customPrompt is None else ""
        
        print("uuid",str(uuid.uuid4()))
        thread_id =request_data.thread_id if request_data.thread_id is not None else str(uuid.uuid4())
        print("thread_id:::::",thread_id)
        agent = RAGAgent(
            system_prompt=prompt,
            tools=[],
            llm=get_active_model(request_data.aiTool),  # Use get_active_model directly
            customPrompt=request_data.customPrompt,
            publication_id=request_data.publication_id if request_data.publication_id else None,
            question_type=request_data.questionType  # Send question type
        )

        questions_response = await agent.run(
            initial_input=request_data.topicTitle if request_data.topicTitle else request_data.customPrompt,
            thread_id=thread_id,
           
        )
        print(questions_response)
        # print(questions_response["response"][0].content)
        current_history=agent.graph.get_state({'configurable': {'thread_id': thread_id}})
        print(":::::current_history:::::::",current_history)
        print(":::::config:::::::",current_history.config)
        print(":::::config Parent Config:::::::",current_history.parent_config)
        checkpoint_id = current_history.config['configurable'].pop('checkpoint_id', None)  # Get checkpoint_id
        parent_checkpointer_id = current_history.parent_config['configurable'].pop('checkpoint_id', None)

        try:
            qcontent = None
            last_question = questions_response["response"][-1]
            try:
                    qcontent = convert_to_clean_json(last_question.content)
                    print(qcontent)
                    
            except Exception as e:
                    print(f"::: error in model Response: {last_question.response_metadata.get('model_name', 'unknown')} ")
                    messageBot = questions_response["response"][0].content
                    print(e)
                    
            question = None
            if qcontent.get('question_text') == '':
                messageBot = questions_response["response"][-1].content
            else:
                question = Question(**{**qcontent, "model_name": last_question.response_metadata.get('model_name', 'unknown')})
            
            print(":::::::clean question", question)
            token_usage_details_list = extract_token_usage_details([questions_response["response"][-1]], num_messages=1)
            for token_usage_details in token_usage_details_list:
                token_usage_details["question_type"] = request_data.questionType
                agent.save_token_usage(thread_id, token_usage_details, request_data.user_id)
        except Exception as e:
            print(e)
            message = str(e).split(": ", 1)[-1]
            token_usage_details_list = extract_token_usage_details([questions_response["response"][-1]], num_messages=1)
            for token_usage_details in token_usage_details_list:
                agent.save_token_usage(thread_id, token_usage_details, request_data.user_id)
            return QuestionResponse(thread_id=str(thread_id),message=messageBot, checkpoint_id=checkpoint_id, parent_checkpointer_id=None)  # Include checkpoint_id   
        # print(questions)
        # response = await llm.generate_question(request, question)
        print("questions:::::",question)
        return QuestionResponse(question=question, question_type=request_data.questionType, thread_id=str(thread_id), checkpoint_id=checkpoint_id, parent_checkpointer_id=parent_checkpointer_id, message=messageBot)  # Include checkpoint_id

@router.post("/reindex", name="reindex_data", dependencies=[Depends(validate_api_key)])
async def reindex_data():
    """
    Reindex the data in the database or search index.

    Returns:
        Response: The response indicating the status of the reindexing operation.
    """
    
    try:
        #initialize vectorstore
        vstorehandler = PineconeVectorStoreHandler()
        vstorehandler.reset_index()
        #load articles
        dataset_folder = "./dataset"
        docs = load_documents_from_folder(dataset_folder)
        vectorstore = vstorehandler.get_vector_store(docs)
        
        return {"status": "success", "message": "Data reindexed successfully"}
    except Exception as e:
        print(e)
        print("Failed to reindex data")
        raise HTTPException(status_code=500, detail=f"Failed to reindex data: {str(e)}")

class DifficultyRequest(BaseModel):
    content: str
    grade: str
    selected_difficulty: Optional[Literal['easy', 'hard']] = 'easy'
    user_id: str = "system"  # Add user_id field

@router.post("/difficultylevel", dependencies=[Depends(validate_api_key)])
async def adjust_difficulty(request: DifficultyRequest):
    """
    Adjust content difficulty based on grade level and selected difficulty.
    """
    try:
        # Filter images before processing
        filtered_content, image_map = filter_images(request.content)
        print("filtered_content", filtered_content)
        agent = DifficultyAgent(llm=get_active_model("gemini"))  # Use get_active_model directly
        result = await agent.run(
            content=filtered_content,
            grade=request.grade,
            difficulty=request.selected_difficulty,
            user_id=request.user_id
        )
        
        # Restore images in the processed content
        processed_content = restore_images(result["response"][-1].content, image_map)
        print("processed_content", processed_content)
        return {
            "status": "success",
            "content": processed_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
