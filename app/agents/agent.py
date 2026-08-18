import logging
import sqlite3
from typing import (
    Annotated,
    Generator,
    Literal,
    TypedDict,
)

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
)
from langchain_openai import ChatOpenAI

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import (
    END,
    START,
    StateGraph,
)
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.config import settings

from langchain_tools import (
    calculator,
    current_time,
    get_weather,
)

from tools.rag_tool import (
    search_documents,
)


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(
    __name__
)


# =========================================================
# MODEL
# =========================================================

model = ChatOpenAI(
    model=settings.model,
)


# =========================================================
# TOOLS
# =========================================================

tools = [
    calculator,
    current_time,
    get_weather,
    search_documents,
]


model_with_tools = model.bind_tools(
    tools
)


# =========================================================
# GRAPH STATE
# =========================================================

class GraphState(TypedDict):

    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]


# =========================================================
# LLM NODE
# =========================================================

def llm_node(
    state: GraphState,
) -> dict:

    logger.debug(
        "LLM node started."
    )

    response = model_with_tools.invoke(
        state["messages"]
    )

    logger.debug(
        "LLM node completed."
    )

    return {
        "messages": [
            response
        ]
    }


# =========================================================
# ROUTER
# =========================================================

def route_after_llm(
    state: GraphState,
) -> Literal[
    "tools",
    "end",
]:

    last_message = state[
        "messages"
    ][-1]

    tool_calls = getattr(
        last_message,
        "tool_calls",
        None,
    )

    if tool_calls:
        return "tools"

    return "end"


# =========================================================
# TOOL NODE
# =========================================================

tool_node = ToolNode(
    tools
)


# =========================================================
# SQLITE MEMORY
# =========================================================

logger.info(
    "Opening memory database: %s",
    settings.rag_agent_memory_db,
)

connection = sqlite3.connect(
    settings.rag_agent_memory_db,
    check_same_thread=False,
)

checkpointer = SqliteSaver(
    connection
)


# =========================================================
# BUILD GRAPH
# =========================================================

builder = StateGraph(
    GraphState
)

builder.add_node(
    "llm",
    llm_node,
)

builder.add_node(
    "tools",
    tool_node,
)

builder.add_edge(
    START,
    "llm",
)

builder.add_conditional_edges(
    "llm",
    route_after_llm,
    {
        "tools": "tools",
        "end": END,
    },
)

builder.add_edge(
    "tools",
    "llm",
)


# =========================================================
# COMPILE GRAPH
# =========================================================

graph = builder.compile(
    checkpointer=checkpointer
)


# =========================================================
# THREAD CONFIG
# =========================================================

def get_config(
    thread_id: str,
) -> dict:

    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


# =========================================================
# ASK AGENT
# =========================================================

def ask_agent(
    user_message: str,
    thread_id: str,
) -> str:

    logger.info(
        "Agent invocation started. thread_id=%s",
        thread_id,
    )

    try:

        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=user_message
                    )
                ]
            },
            config=get_config(
                thread_id
            ),
        )

        messages = result.get(
            "messages",
            [],
        )

        if not messages:

            logger.warning(
                "Agent returned no messages. thread_id=%s",
                thread_id,
            )

            return ""

        final_message = messages[-1]

        content = getattr(
            final_message,
            "content",
            "",
        )

        logger.info(
            "Agent invocation completed. thread_id=%s",
            thread_id,
        )

        return str(
            content
        )

    except Exception:

        logger.exception(
            "Agent invocation failed. thread_id=%s",
            thread_id,
        )

        raise


# =========================================================
# STREAM AGENT
# =========================================================

def stream_agent(
    user_message: str,
    thread_id: str,
) -> Generator[
    str,
    None,
    None,
]:
    """
    LangGraph state updates stream garee.

    Fiiro:
    Tani waa chunk/state streaming,
    ma aha token-by-token streaming.
    """

    logger.info(
        "Agent streaming started. thread_id=%s",
        thread_id,
    )

    previous_content = ""

    try:

        for event in graph.stream(
            {
                "messages": [
                    HumanMessage(
                        content=user_message
                    )
                ]
            },
            config=get_config(
                thread_id
            ),
            stream_mode="values",
        ):

            messages = event.get(
                "messages",
                [],
            )

            if not messages:
                continue

            last_message = messages[-1]

            message_type = getattr(
                last_message,
                "type",
                "",
            )

            # Tool messages user-ka si toos ah
            # uma stream gareyneyno.
            if message_type != "ai":
                continue

            content = getattr(
                last_message,
                "content",
                "",
            )

            if not isinstance(
                content,
                str,
            ):
                content = str(
                    content
                )

            content = content.strip()

            if not content:
                continue

            # stream_mode="values" wuxuu soo celin karaa
            # state isku mid ah marar badan.
            if content == previous_content:
                continue

            previous_content = content

            yield content

        logger.info(
            "Agent streaming completed. thread_id=%s",
            thread_id,
        )

    except Exception:

        logger.exception(
            "Agent streaming failed. thread_id=%s",
            thread_id,
        )

        raise


# =========================================================
# GET THREAD HISTORY
# =========================================================

def get_thread_history(
    thread_id: str,
) -> list[dict]:

    logger.info(
        "Reading thread history. thread_id=%s",
        thread_id,
    )

    config = get_config(
        thread_id
    )

    snapshot = graph.get_state(
        config
    )

    values = snapshot.values or {}

    messages = values.get(
        "messages",
        [],
    )

    history = []

    for message in messages:

        message_type = getattr(
            message,
            "type",
            "",
        )

        if message_type == "human":
            role = "user"

        elif message_type == "ai":
            role = "assistant"

        elif message_type == "tool":
            role = "tool"

        elif message_type == "system":
            role = "system"

        else:
            role = "unknown"

        content = getattr(
            message,
            "content",
            "",
        )

        history.append(
            {
                "role": role,
                "content": str(
                    content
                ),
            }
        )

    return history


# =========================================================
# CLOSE AGENT
# =========================================================

def close_agent() -> None:

    logger.info(
        "Closing LangGraph memory connection."
    )

    connection.close()


# =========================================================
# LOCAL TEST
# =========================================================

def main() -> None:

    thread_id = (
        "lesson25-agent-test"
    )

    print(
        "🤖 Agent Test"
    )

    print(
        "Qor exit si aad uga baxdo.\n"
    )

    while True:

        message = input(
            "Adiga: "
        ).strip()

        if message.lower() == "exit":

            close_agent()

            print(
                "Nabadgelyo!"
            )

            break

        if not message:
            continue

        try:

            answer = ask_agent(
                user_message=message,
                thread_id=thread_id,
            )

            print(
                f"\nAgent: {answer}\n"
            )

        except Exception as error:

            print(
                f"\nError: {error}\n"
            )


if __name__ == "__main__":
    main()