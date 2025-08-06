from datetime import datetime
from fastapi import APIRouter, WebSocket, HTTPException, Depends, Request, FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import asyncio
from utilities.llm.assistant_agent import AssistantAgent
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage

from utilities.llm.ai_factory import AIFactory
from utilities.llm.chain import run_chain
from utilities.llm.prompts.assistant_prompt import ASSISTANT_SYSTEM_PROMPT, WEB_ASSISTANT_SYSTEM_PROMPT
from utilities.llm.prompts.title_suggestion_prompt import TITLE_SUGGESTION_PROMPT
from utilities.database.models.history_listing import HistoryListing
from utilities.database.models.search_index import SearchIndex
from utilities.database.models.checkpoints import Checkpoints
from utilities.database.models.checkpoint_writes import CheckpointWrites
import logging
import uuid
from utilities.helper import extract_token_usage_details
from utilities.llm.tools.content_search_tool import content_search
from utilities.llm.tools.sample_tool import get_weather
from core.model_config import get_active_model
from fastapi import Body, Query

from utilities.llm.tools.support_search_tool import support_search

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str
    thread_id: Optional[str] = "default"
    publication_ids_array: Optional[list[str]] = None
    focus: Optional[str] = None  # Add focus flag

class TitleRequest(BaseModel):
    user_id: str
    thread_id: str
    query: str

class TitleResponse(BaseModel):
    thread_id: str
    title: str
    id:str

async def stream_response(system_prompt: str, request: ChatRequest):
    try:
        agent = AssistantAgent(
            system_prompt=system_prompt,
            llm=get_active_model("gemini"),
            tools=[content_search],
            info={"publication_id": request.publication_ids_array}
        )
        async for chunk in agent.run(
            initial_input=request.message, thread_id=request.thread_id
        ):
            # print(f"Chunk received: {chunk}")  # Debug log
            if isinstance(chunk, dict):
                yield f"data: {json.dumps(chunk)}\n\n"
            else:
                yield f"data: {json.dumps({'content': str(chunk)})}\n\n"
    except Exception as e:
        logging.error(e)  # Debug log   
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    try:
        print(f"Received request: {request}")  # Debug log
        
        if not request.message:
            raise ValueError("Message cannot be empty")
            
        system_prompt = ASSISTANT_SYSTEM_PROMPT
        
        return StreamingResponse(
            stream_response(system_prompt=system_prompt, request=request),
            media_type="text/event-stream"
        )

    except Exception as e:
        print(f"Error in chat_stream: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/")
async def chat(request: ChatRequest):
    try:
        if not request.message:
            raise ValueError("Message cannot be empty")
        print(f"Received request: {request}")  
        
        agent_info ={}
        if request.focus == "web":
            system_prompt = WEB_ASSISTANT_SYSTEM_PROMPT
            tools = []
        elif request.focus == "swo":
            system_prompt = ASSISTANT_SYSTEM_PROMPT
            if request.publication_ids_array and str(request.publication_ids_array).strip() not in ["", "[]", "null", None]:
                system_prompt += "\n Note user only subscribed to the following publications :" + str(request.publication_ids_array)
            tools = [content_search, support_search]
            agent_info = {"publication_ids": request.publication_ids_array}
        else:
            system_prompt = ASSISTANT_SYSTEM_PROMPT
            tools = []

        thread_id = request.thread_id if request.thread_id is not None else str(uuid.uuid4())
        if request.focus:
            agent_info["focus"] = request.focus
            agent_info["user_id"] = request.user_id
            agent_info["thread_id"] = thread_id


        agent = AssistantAgent(
            system_prompt=system_prompt,
            llm=get_active_model("gemini"),
            tools=tools,
            info=agent_info,
            
        )
        state = {"messages": [{"role":"human", "content": request.message}]}
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 1500,
        }
        result = agent.graph.invoke(state, config)
        messages = result.get("messages", [])
        print(f"****Messages received: {messages}")
        formatted_messages = []
        internal_source_url = None
        for msg in messages:
            # If msg is not a dict (e.g., a HumanMessage object), convert to dict or extract needed fields
            if isinstance(msg, BaseMessage) and msg.content:
                formatted = {
                    "id": msg.id,
                    "type": msg.type,
                    "content": msg.content
                }
                formatted_messages.append(formatted)
                if isinstance(msg, ToolMessage)  and isinstance(json.loads(msg.content), dict):
                    print(f"--------Tool message content: {msg.content}")
                    internal_source_url= json.loads(msg.content).get("internal_source_url", None)
                    # split the internal_source_url with "/" take the last part as search_index_id
                    if internal_source_url:
                        print(internal_source_url)
                        search_index_id = internal_source_url.split("/")[-1]
                        
            elif isinstance(msg, BaseMessage):
                formatted = {
                    "id": msg.id,
                    "type": msg.type,
                    "tool_calls": msg.tool_calls if hasattr(msg, "tool_calls") else []
                }
                formatted_messages.append(formatted)
               
        try:
            if internal_source_url and search_index_id:
                SearchIndex.objects(id=search_index_id).update(
                    set__final_answer=messages[-1].content if messages else "",
                    set__checkpointer_id=messages[-1].id if messages else None,
                    set__thread_id=thread_id,
                    set__user_id=request.user_id,
                    set__created_at=datetime.now()
                )
        except Exception as e:
            logging.error(f"Failed to update to SearchIndex: {e}")

        # Save token usage for the last message using agent type assistant
        # try:
        #    if messages:
        #         token_usage_details_list = extract_token_usage_details([messages[-1]], num_messages=1)
        #         for token_usage_details in token_usage_details_list:
        #             token_usage_details["focus"] = getattr(request, "focus", None)
        #             agent.save_token_usage(thread_id, token_usage_details, request.user_id)
        # except Exception as e:
        #     logging.error(f"Failed to save token usage: {e}")

        finalmessage = messages[-1].content if messages and isinstance(messages[-1], AIMessage) else messages[-1].type
        return {
            "thread_id": thread_id,
            "messages": formatted_messages,
            "finalmessage": finalmessage,
        }
    except Exception as e:
        print(e)
        logging.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/thread", response_model=TitleResponse)
async def generate_title(request: TitleRequest):
     
    result = run_chain(
        prompt_template=TITLE_SUGGESTION_PROMPT,
        model_name="gemini",  
        query=request.query
    )
    if isinstance(result, dict) and "title" in result:
        generated_title = result["title"]
    else:
        generated_title = str(result).strip()[:50] or "Untitled"

    
    obj = HistoryListing.objects(thread_id=request.thread_id, user_id=request.user_id).modify(
        upsert=True,
        new=True,
        set__title=generated_title,
        set__created_at=datetime.now(),
    )
    print(obj)
    obj_id = str(obj.id) if obj and obj.id else None
    return TitleResponse(thread_id=request.thread_id, title=generated_title, id=obj_id)

# New endpoint to list all threads for a given user id
class HistoryListingRequest(BaseModel):
    user_id: str

class HistoryListingResponse(BaseModel):
    thread_id: str
    title: Optional[str] = None
    id: str

@router.post("/thread/listing", response_model=list[HistoryListingResponse])
async def get_history_listing(request: HistoryListingRequest):
    threads = HistoryListing.objects(user_id=request.user_id)
    return [
        HistoryListingResponse(thread_id=thread.thread_id, title=thread.title, id=str(thread.id))
        for thread in threads
    ]

class SearchIndexMetaRequest(BaseModel):
    id: str
    publication_ids_array: list[str]

@router.post("/search")
async def get_search_index_meta(request: SearchIndexMetaRequest):
    # Fetch the record from search_index collection
    record = SearchIndex.objects(id=request.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="SearchIndex record not found")

    query = record.query
    # Call content_search tool with the query and publication_ids_array, top_k=20
    from utilities.llm.tools.content_search_tool import content_search
    try:
        content_search_response = content_search.invoke(input={
            "query": query,
            "top_k": 20,
            "publication_ids_array": request.publication_ids_array
        })
        print("content_search_response--->",content_search_response)
        # Parse the response and extract only metadata
        
        docs = []
        try:
            docs = json.loads(content_search_response)
        except Exception:
            docs = []
        metadata_list = [doc.get("metadata", {}) for doc in docs if isinstance(doc, dict) and "metadata" in doc]
        return {"metadata": metadata_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in content search: {str(e)}")

@router.get("/thread/{thread_id}")
async def load_conversation(thread_id: str):
    try:
        # Reconstruct the agent with default system prompt and tools
        agent = AssistantAgent(
            system_prompt=ASSISTANT_SYSTEM_PROMPT,
            llm=get_active_model("gemini"),
            tools=[content_search],
            info={}
        )
        
        # Get the conversation state for the thread
        state = agent.graph.get_state({'configurable': {'thread_id': thread_id}})
        print(f"Loaded state for thread {thread_id}: {state}")  
        # Access messages from state.values if StateSnapshot
        messages = state.values.get("messages", []) if hasattr(state, "values") else []
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, ToolMessage):
                continue
            
            # Format both AI and Human messages in the same way
            if isinstance(msg, (AIMessage, HumanMessage)) and msg.content:
                formatted = {
                    "id": msg.id,
                    "type": msg.type,
                    "content": msg.content
                }
                formatted_messages.append(formatted)
        return {"messages": formatted_messages}
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/message")
async def get_search_index_by_message_id(mid: str = Query(..., description="Message ID to search for")):
    """
    Get all search_index records with the given checkpointer_id (message_id).
    """
    records = SearchIndex.objects(checkpointer_id=mid)
    results = []
    for rec in records:
        results.append({
            "id": str(rec.id),
            "final_answer": rec.final_answer,
            "query": rec.query,
            "sources": rec.sources,
            "thread_id": rec.thread_id,
            "user_id": rec.user_id,
            "checkpointer_id": rec.checkpointer_id,
        })
    return {"results": results}

class RenameRequest(BaseModel):
    id: str
    title: str

@router.put("/thread", response_model=TitleResponse)
async def rename_title(request: RenameRequest):
    obj = HistoryListing.objects(id=request.id).modify(
        new=True,
        set__title=request.title
    )
    
    if not obj:
        raise HTTPException(status_code=404, detail="History listing not found")
        
    return TitleResponse(thread_id=obj.thread_id, title=obj.title, id=str(obj.id))

class DeleteThreadRequest(BaseModel):
    thread_id: str

@router.delete("/thread")
async def delete_thread(request: DeleteThreadRequest):
    try:
        print("thread id ", request.thread_id)
        # Delete from HistoryListing
        history_result = HistoryListing.objects(thread_id=request.thread_id).delete()
        
        # Delete from CheckpointWrites
        checkpoint_writes_result = CheckpointWrites.objects(thread_id=request.thread_id).delete()
        
        # Delete from Checkpoints
        checkpoints_result = Checkpoints.objects(thread_id=request.thread_id).delete()
        
        if not (history_result or checkpoint_writes_result or checkpoints_result):
            raise HTTPException(status_code=404, detail="Thread not found")
            
        return {"message": "Thread deleted successfully", "thread_id": request.thread_id}
    except Exception as e:
        logging.error(f"Error deleting thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))




