from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    name: str
    memory: Annotated[list, add_messages]
    summary: str