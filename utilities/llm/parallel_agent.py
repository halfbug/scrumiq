import json
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from core.config import config
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from langgraph.graph import START,END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from typing import Annotated, Any, Dict, List
import operator
import os
from datetime import datetime

from utilities.llm.ai_factory import AIFactory
from utilities.vectorstore import PineconeVectorStoreHandler

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

class AgentState(MessagesState):
    input: str
    context: str
    response: Annotated[List[str], operator.add]

class ParallelAgent:
    def __init__(self, system_prompt: PromptTemplate, tools: list, llm: str, customPrompt: str | None = None, publication_id: str | None = None):
        """
        Initializes the GraphAgent.

        Args:
            system_prompt: The system prompt for the LLM.
            tools: A list of tool functions.
            llm: The model name to use.
            customPrompt: Optional custom prompt.
            publication_id: Optional publication ID for filtering.
        """
        self.system_prompt = system_prompt
        self.tools = tools if tools else []
        self.llm = llm
        self.customPrompt = customPrompt
        self.publication_id = publication_id
        self.graph = self._build_graph()
    
    def get_system_prompt(self, state: AgentState):
        """Returns the formatted system prompt."""
        # print("customPrompt:::::::::::", self.customPrompt)
        # print("system_prompt:::::::::::", self.system_prompt.format(context=state["context"]))
        if self.customPrompt is None:
            # print(self.system_prompt.format(context=state["context"]))
            return [SystemMessage(content=self.system_prompt.format(context=state["context"]))] + state["messages"]  
        else : 
            return state["messages"] 
    
    def _build_graph(self):
        """Builds the LangGraph execution graph."""
        # sys_msg = SystemMessage(content=self.system_prompt.format(context=state["context"]))
        # llm_with_tools = self.llm.bind_tools(self.tools, parallel_tool_calls=False)

        def initalize(state: AgentState):
            # print("Initializer Node ::::::::::: ", state)

            query = state["messages"][-1].content
            print(query)
            if self.system_prompt is not None:
                handler = PineconeVectorStoreHandler()
                vectorstore = handler.get_vector_store()
                filter_criteria = {"publication_id": self.publication_id} if self.publication_id else {}
                context =vectorstore.similarity_search(  
                    query,  # our search query  
                    k=3,  # return 3 most relevant docs  
                    filter=filter_criteria
                )
                context = format_docs(context)  
            return {"input": state["messages"][-1].content, "response":[], "context": context if len(context) > 0 else " "}
            

        def model_node(state: AgentState):
            print(f"Using model: {self.llm}")
            response = AIFactory.get_tool(self.llm).use(self.get_system_prompt(state))
            print("response::::::::::::", response)
            return {"response": [response], "messages": [response]}

        builder = StateGraph(AgentState)
        
        builder.add_node("initialize", initalize)
        builder.add_node("model", model_node)

        builder.add_edge(START, "initialize")
        builder.add_edge("initialize", "model")
        builder.add_edge("model", END)
        
        mongodb_client = MongoClient(os.environ["MONGO_URI"])
        mongodb_saver = MongoDBSaver(mongodb_client, os.environ['MONGO_DB'])    
        memory = MemorySaver()
        graph = builder.compile(checkpointer=mongodb_saver)
        return graph

    def save_token_usage(self, thread_id: str, token_usage_details: Dict[str, Any], user_id: str):
        """Saves the token usage details to the MongoDB collection."""
        mongodb_client = MongoClient(os.environ["MONGO_URI"])
        db = mongodb_client[os.environ['MONGO_DB']]
        collection = db["tokenz"]
        token_usage_details.update({
            "thread_id": thread_id,
            "user_id": user_id,
            "update_time": datetime.utcnow()
        })
        collection.insert_one(token_usage_details)

    async def run(self, initial_input: str, thread_id: str = "2", user_id: str = "unknown"):
        """
        Runs the agent with the given initial input.

        Args:
            initial_input: The initial user input.
            thread_id: Optional. The ID of the thread to track. Defaults to "2".
            user_id: Optional. The ID of the user. Defaults to "unknown".
        """
        initial_state = {"messages": [HumanMessage(content=initial_input)]}
        thread = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 1500,
        }  # Now uses the passed thread_id
        return self.graph.invoke(initial_state, thread)

