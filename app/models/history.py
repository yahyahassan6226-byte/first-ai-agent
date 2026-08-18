from pydantic import BaseModel


class HistoryMessage(BaseModel):
    role: str
    content: str


class ConversationHistoryResponse(BaseModel):
    thread_id: str
    count: int
    messages: list[HistoryMessage]