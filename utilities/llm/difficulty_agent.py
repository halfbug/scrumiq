import uuid
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import START, END, MessagesState, StateGraph
from typing import Annotated, List
import operator
from utilities.llm.ai_factory import AIFactory
from utilities.database.usage_tracker import UsageTracker
from utilities.helper import extract_token_usage_details

class DifficultyState(MessagesState):
    content: str
    grade: str
    difficulty: str
    response: Annotated[List[str], operator.add]

class DifficultyAgent:
    def __init__(self, llm: str):
        self.llm = llm
        self.graph = self._build_graph()
        self.usage_tracker = UsageTracker()
        self.system_prompt = """Adapt educational content for {grade} grade, {difficulty} difficulty.
Rules:
1. Keep all placeholders (format: __TYPE##__)
2. Preserve HTML format
3. difficulty='hard': use advanced vocabulary
4. difficulty='easy': simplify language
5. Match grade level concepts
6. Only modify text difficulty"""

    def _build_graph(self):
        def model_node(state: DifficultyState):
            prompt = self.system_prompt.format(
                grade=state["grade"],
                difficulty=state["difficulty"]
            )
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=state["content"])
            ]
            response = AIFactory.get_tool(self.llm).use(messages)
            return {"response": [response]}

        builder = StateGraph(DifficultyState)
        builder.add_node("model", model_node)
        builder.add_edge(START, "model")
        builder.add_edge("model", END)
        
        return builder.compile()

    async def run(self, content: str, grade: str, difficulty: str, user_id: str = "system"):
        initial_state = {
            "content": content,
            "grade": grade,
            "difficulty": difficulty,
        }
        result = self.graph.invoke(initial_state)
        
        # Track token usage
        token_usage_details_list = extract_token_usage_details([result["response"][-1]], num_messages=1)
        for token_usage_details in token_usage_details_list:
            token_usage_details["difficulty_level"] =  difficulty
            self.usage_tracker.save_usage(
                thread_id=str(result.get("thread_id", str(uuid.uuid4()))),
                usage_details=token_usage_details,
                user_id=user_id,
                agent_type="difficulty"
            )
        
        return result
