import json
import logging
from typing import Any, Dict
from pymongo import MongoClient
import os
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.mongodb import MongoDBSaver

from utilities.database.usage_tracker import UsageTracker
from utilities.helper import get_message_token_usage
from utilities.llm.ai_factory import AIFactory




class AssistantAgent:
    def __init__(self, system_prompt: str, tools: list, llm, info: dict = None):
        """
        Initializes the GraphAgent.

        Args:
            system_prompt: The system prompt for the LLM.
            tools: A list of tool functions.
            llm: The language model instance.
            info: Optional dictionary containing additional information like publication_id.
        """
        self.system_prompt = system_prompt
        self.tools = tools
        self.llm = llm
        self.info = info or {}
        self.graph = self._build_graph()
        self.usage_tracker = UsageTracker()
        

    def save_token_usage(self, thread_id: str, token_usage_details: Dict[str, Any], user_id: str):
        """Saves the token usage details using UsageTracker."""
        self.usage_tracker.save_usage(thread_id, token_usage_details, user_id, agent_type="assistant", model_name = self.llm)
    

    def _build_graph(self):
        """Builds the LangGraph execution graph."""
        sys_msg = SystemMessage(content=self.system_prompt)
        logging.info(f"tools: {self.tools}")
        llm_with_tools = AIFactory.get_tool(self.llm, tools=self.tools)


        def assistant(state: MessagesState):
            # print("Prompt ::::::::::: ", [sys_msg] + state["messages"])
            aimessage = [llm_with_tools.use([sys_msg] + self.get_last_interaction(state["messages"]))]
            messageUseageDetails = get_message_token_usage(aimessage[0])
            if messageUseageDetails is not None:
                self.save_token_usage(self.info.get("thread_id"), messageUseageDetails, self.info.get("user_id"))
            return {"messages": aimessage}



        builder = StateGraph(MessagesState)
        builder.add_node("assistant", assistant)
        builder.add_node("tools", ToolNode(self.tools))
        builder.add_edge(START, "assistant")
        builder.add_conditional_edges(
            "assistant",
            tools_condition,
        )
        builder.add_edge("tools", "assistant")
        builder.add_edge("assistant", END)

        mongodb_client = MongoClient(os.environ["MONGO_URI"])
        mongodb_saver = MongoDBSaver(mongodb_client, os.environ['MONGO_DB'])    
        # memory = MemorySaver()
        graph = builder.compile(checkpointer=mongodb_saver)
        return graph


    async def run(self, initial_input: str, thread_id: str = "2"):
        """
        Runs the agent with the given initial input.

        Args:
            initial_input: The initial user input.
            thread_id: Optional. The ID of the thread to track. Defaults to "2".
        """
        initial_state = {"messages": [HumanMessage(content=initial_input)]}
        self.thread_id = thread_id
        thread = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 1500,
        }

        response = {"response": []}
        
        async for chunk in self.graph.astream(
            initial_state, thread, stream_mode="values"
        ):
            last_message = chunk["messages"][-1]
            last_message.pretty_print()
            print(last_message)

            # Handle tool calls
            if (
                isinstance(last_message, AIMessage)
                and last_message.tool_calls):
                action_message = {"type": "action"}
                print("Tool calls found in AIMessage")
                for tool_call in last_message.tool_calls:
                    action_message = {
                        "type": "action",
                        "tool": tool_call["name"],
                        "tool_input":tool_call["args"],

                    }
                    # response["response"].append(action_message)
                yield action_message

            # Handle tool responses
            elif isinstance(last_message, ToolMessage):
                step_message = {
                    "type": "observation",
                    "result": last_message.content,
                }
                # response["response"].append(step_message)
                yield step_message

            # Handle final output
            elif (
                isinstance(last_message, AIMessage) and
                last_message.content
            ):
                final_output_message = {
                    "type": "final_output",
                    "message": last_message.content,
                }
                # response["response"].append(final_output_message)
                yield final_output_message

        # return response


    def get_last_interaction(self, messages):

        if len(messages) > 4:
            for idx in range(len(messages) - 2, -1, -1):
                if isinstance(messages[idx], HumanMessage):
                    return messages[idx:]
        return messages


