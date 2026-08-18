from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# =========================================================
# CHAT REQUEST
# =========================================================

class ChatRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "Waa maxay RAG?",
                    "thread_id": "lesson25-demo",
                }
            ]
        }
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message-ka loo dirayo AI Agent-ka.",
    )

    thread_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description=(
            "Conversation thread ID. "
            "Haddii aan la bixin, server-ku mid cusub ayuu sameynayaa."
        ),
    )


# =========================================================
# CHAT RESPONSE
# =========================================================

class ChatResponse(BaseModel):
    success: bool
    thread_id: str
    answer: str
    error: str | None = None


# =========================================================
# THREAD RESPONSE
# =========================================================

class ThreadResponse(BaseModel):
    thread_id: str
    status: str


# =========================================================
# ERROR DETAIL
# =========================================================

class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


# =========================================================
# ERROR BODY
# =========================================================

class ErrorBody(BaseModel):
    type: str
    message: str
    details: list[ErrorDetail] | None = None


# =========================================================
# STANDARD ERROR RESPONSE
# =========================================================

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody


# =========================================================
# GENERIC DATA RESPONSE
# =========================================================

class GenericResponse(BaseModel):
    success: bool
    data: dict[str, Any] | None = None