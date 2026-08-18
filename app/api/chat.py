import json
import logging

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from fastapi.responses import (
    StreamingResponse,
)

from app.models.chat import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    ThreadResponse,
)

from app.models.history import (
    ConversationHistoryResponse,
    HistoryMessage,
)

from app.services.agent_service import (
    chat_with_agent,
    get_conversation_history,
    get_thread_status,
    stream_with_agent,
)


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(
    __name__
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    tags=["Chat"],
)


# =========================================================
# NORMAL CHAT ENDPOINT
# =========================================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with AI Agent",
    description=(
        "Send a message to the "
        "LangGraph AI Agent."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": (
                "Invalid request or agent failure."
            ),
        },
    },
)
def chat(
    request: ChatRequest,
) -> ChatResponse:

    logger.info(
        "Chat request received. thread_id=%s",
        request.thread_id,
    )

    result = chat_with_agent(
        message=request.message,
        thread_id=request.thread_id,
    )

    if not result.success:

        logger.warning(
            "Agent request failed. "
            "thread_id=%s error=%s",
            request.thread_id,
            result.error,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                result.error
                or "Agent request failed."
            ),
        )

    logger.info(
        "Chat request completed. thread_id=%s",
        result.thread_id,
    )

    return ChatResponse(
        success=True,
        thread_id=result.thread_id,
        answer=result.answer,
        error=None,
    )


# =========================================================
# STREAM CHAT ENDPOINT
# =========================================================

@router.post(
    "/chat/stream",
    summary="Stream AI Agent response",
    description=(
        "Send a message to the LangGraph Agent "
        "and receive NDJSON streamed chunks."
    ),
)
def chat_stream(
    request: ChatRequest,
) -> StreamingResponse:

    logger.info(
        "Streaming chat request received. thread_id=%s",
        request.thread_id,
    )

    try:

        thread_id, generator = stream_with_agent(
            message=request.message,
            thread_id=request.thread_id,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(
                error
            ),
        )

    def event_stream():

        # ---------------------------------------------
        # THREAD EVENT
        # ---------------------------------------------

        yield (
            json.dumps(
                {
                    "type": "thread",
                    "thread_id": thread_id,
                },
                ensure_ascii=False,
            )
            + "\n"
        )

        try:

            # -----------------------------------------
            # CONTENT EVENTS
            # -----------------------------------------

            for chunk in generator:

                yield (
                    json.dumps(
                        {
                            "type": "chunk",
                            "content": chunk,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

            # -----------------------------------------
            # DONE EVENT
            # -----------------------------------------

            yield (
                json.dumps(
                    {
                        "type": "done",
                        "thread_id": thread_id,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

            logger.info(
                "Streaming request completed. thread_id=%s",
                thread_id,
            )

        except Exception as error:

            logger.exception(
                "Streaming endpoint failed. thread_id=%s",
                thread_id,
            )

            yield (
                json.dumps(
                    {
                        "type": "error",
                        "message": (
                            "Streaming failed: "
                            f"{type(error).__name__}: "
                            f"{error}"
                        ),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    return StreamingResponse(
        event_stream(),
        media_type=(
            "application/x-ndjson"
        ),
        headers={
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )


# =========================================================
# THREAD STATUS
# =========================================================

@router.get(
    "/threads/{thread_id}",
    response_model=ThreadResponse,
    summary="Get thread status",
)
def get_thread(
    thread_id: str,
) -> ThreadResponse:

    logger.info(
        "Thread status request. thread_id=%s",
        thread_id,
    )

    try:

        result = get_thread_status(
            thread_id
        )

        return ThreadResponse(
            thread_id=result[
                "thread_id"
            ],
            status=result[
                "status"
            ],
        )

    except ValueError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(
                error
            ),
        )


# =========================================================
# CONVERSATION HISTORY
# =========================================================

@router.get(
    "/threads/{thread_id}/history",
    response_model=(
        ConversationHistoryResponse
    ),
    summary="Get conversation history",
)
def conversation_history(
    thread_id: str,
) -> ConversationHistoryResponse:

    logger.info(
        "History endpoint requested. thread_id=%s",
        thread_id,
    )

    try:

        result = get_conversation_history(
            thread_id
        )

        messages = [
            HistoryMessage(
                role=item[
                    "role"
                ],
                content=item[
                    "content"
                ],
            )
            for item
            in result[
                "messages"
            ]
        ]

        return ConversationHistoryResponse(
            thread_id=result[
                "thread_id"
            ],
            count=result[
                "count"
            ],
            messages=messages,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(
                error
            ),
        )

    except Exception as error:

        logger.exception(
            "Conversation history failed. "
            "thread_id=%s",
            thread_id,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Conversation history "
                f"could not be loaded: {error}"
            ),
        )