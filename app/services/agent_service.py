import logging
from dataclasses import dataclass
from typing import (
    Generator,
    Optional,
)
from uuid import uuid4

from app.agents.agent import (
    ask_agent,
    get_thread_history,
    stream_agent,
)


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(
    __name__
)


# =========================================================
# SERVICE RESPONSE
# =========================================================

@dataclass
class AgentResponse:
    success: bool
    thread_id: str
    answer: str
    error: Optional[str] = None


# =========================================================
# CREATE THREAD
# =========================================================

def create_thread_id() -> str:

    return str(
        uuid4()
    )


# =========================================================
# VALIDATE THREAD
# =========================================================

def validate_thread_id(
    thread_id: str | None,
) -> str:

    if thread_id is None:
        return create_thread_id()

    thread_id = thread_id.strip()

    if not thread_id:
        return create_thread_id()

    if len(thread_id) > 100:

        raise ValueError(
            "thread_id aad ayuu u dheer yahay."
        )

    return thread_id


# =========================================================
# VALIDATE MESSAGE
# =========================================================

def validate_message(
    message: str,
) -> str:

    if not isinstance(
        message,
        str,
    ):

        raise ValueError(
            "Message-ku waa inuu noqdaa text."
        )

    message = message.strip()

    if not message:

        raise ValueError(
            "Message-ku madhan ma noqon karo."
        )

    if len(message) > 10000:

        raise ValueError(
            "Message-ku aad ayuu u dheer yahay."
        )

    return message


# =========================================================
# CHAT WITH AGENT
# =========================================================

def chat_with_agent(
    message: str,
    thread_id: str | None = None,
) -> AgentResponse:

    clean_thread_id = ""

    try:

        clean_message = validate_message(
            message
        )

        clean_thread_id = validate_thread_id(
            thread_id
        )

        logger.info(
            "Calling agent. thread_id=%s",
            clean_thread_id,
        )

        answer = ask_agent(
            user_message=clean_message,
            thread_id=clean_thread_id,
        )

        if not answer:

            logger.warning(
                "Agent returned empty answer. thread_id=%s",
                clean_thread_id,
            )

            return AgentResponse(
                success=False,
                thread_id=clean_thread_id,
                answer="",
                error=(
                    "Agent-ku jawaab ma soo saarin."
                ),
            )

        logger.info(
            "Agent completed successfully. thread_id=%s",
            clean_thread_id,
        )

        return AgentResponse(
            success=True,
            thread_id=clean_thread_id,
            answer=answer,
            error=None,
        )

    except ValueError as error:

        logger.warning(
            "Validation error. error=%s",
            error,
        )

        return AgentResponse(
            success=False,
            thread_id=(
                clean_thread_id
                or thread_id
                or ""
            ),
            answer="",
            error=str(
                error
            ),
        )

    except Exception as error:

        logger.exception(
            "Unexpected agent service error."
        )

        return AgentResponse(
            success=False,
            thread_id=(
                clean_thread_id
                or thread_id
                or ""
            ),
            answer="",
            error=(
                "Agent service error: "
                f"{type(error).__name__}: "
                f"{error}"
            ),
        )


# =========================================================
# STREAM WITH AGENT
# =========================================================

def stream_with_agent(
    message: str,
    thread_id: str | None = None,
) -> tuple[
    str,
    Generator[
        str,
        None,
        None,
    ],
]:
    """
    Message + thread validate garee,
    kadib Agent generator soo celi.
    """

    clean_message = validate_message(
        message
    )

    clean_thread_id = validate_thread_id(
        thread_id
    )

    logger.info(
        "Streaming service started. thread_id=%s",
        clean_thread_id,
    )

    generator = stream_agent(
        user_message=clean_message,
        thread_id=clean_thread_id,
    )

    return (
        clean_thread_id,
        generator,
    )


# =========================================================
# THREAD STATUS
# =========================================================

def get_thread_status(
    thread_id: str,
) -> dict:

    clean_thread_id = validate_thread_id(
        thread_id
    )

    logger.info(
        "Thread status requested. thread_id=%s",
        clean_thread_id,
    )

    return {
        "thread_id": clean_thread_id,
        "status": "available",
    }


# =========================================================
# CONVERSATION HISTORY
# =========================================================

def get_conversation_history(
    thread_id: str,
) -> dict:

    clean_thread_id = validate_thread_id(
        thread_id
    )

    logger.info(
        "Conversation history requested. thread_id=%s",
        clean_thread_id,
    )

    messages = get_thread_history(
        clean_thread_id
    )

    return {
        "thread_id": clean_thread_id,
        "count": len(
            messages
        ),
        "messages": messages,
    }


# =========================================================
# LOCAL TEST
# =========================================================

def main() -> None:

    response = chat_with_agent(
        message="Waa maxay RAG?",
        thread_id="lesson25-service-test",
    )

    print(
        response
    )


if __name__ == "__main__":
    main()