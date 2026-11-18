
from typing import TypedDict


class AgentState(TypedDict):
    session_id: str
    question: str
    history: list
    intent: str
    confidence: float
    answer: str
    sources: list
    handoff: bool
