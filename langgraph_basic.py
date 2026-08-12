import sqlite3
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
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

from config import MODEL

from langchain_tools import (
    calculator,
    current_time,
    get_weather,
    list_recent_emails,
    read_email,
    search_emails,
)

from tools.gmail_tool import create_draft


# =========================================================
# MODEL
# =========================================================

model = ChatOpenAI(
    model=MODEL,
)


# =========================================================
# SAFE READ-ONLY / NON-WRITE TOOLS
# =========================================================

tools = [
    calculator,
    current_time,
    get_weather,
    list_recent_emails,
    search_emails,
    read_email,
]


model_with_tools = model.bind_tools(
    tools
)


# =========================================================
# GRAPH STATE
# =========================================================

class AgentState(TypedDict):
    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    pending_draft_to: str
    pending_draft_subject: str
    pending_draft_body: str

    draft_requested: bool
    approved: bool

    draft_result: str
    error: str


# =========================================================
# SYSTEM INSTRUCTIONS
# =========================================================

SYSTEM_PROMPT = """
You are a helpful multi-step AI assistant.

Respond in the same language as the user.

Use conversation history for follow-up questions.

You have tools for:
- calculator
- current time
- weather
- recent Gmail emails
- Gmail search
- Gmail read

You may use multiple tools sequentially.

If the user asks to find an email and then read or summarize it:
1. search_emails
2. get the Message ID
3. read_email
4. answer from the returned email content

If the user asks to prepare a reply:
- read the original email first when necessary
- prepare a professional reply
- do not claim it was sent

IMPORTANT GMAIL SAFETY:

You do NOT have a send-email tool.

Never claim that an email was sent.

Do NOT create Gmail drafts through normal tool calls.

If the user explicitly asks to SAVE or CREATE a Gmail draft,
prepare the recipient, subject, and body in your final answer
using exactly this machine-readable format:

DRAFT_REQUEST
TO: recipient@example.com
SUBJECT: subject here
BODY:
email body here
END_DRAFT

Only produce DRAFT_REQUEST when the user explicitly asks
to save/create a Gmail draft.

If the user only asks to write or prepare a reply,
return the reply as ordinary text.

Never invent email content, sender, subject, or recipient.

If a tool fails, do not claim success.
"""


# =========================================================
# LLM NODE
# =========================================================

def llm_node(
    state: AgentState,
) -> dict:
    """
    Model-ka u dir conversation history-ga oo dhan.
    """

    messages = state["messages"]

    response = model_with_tools.invoke(
        [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *messages,
        ]
    )

    return {
        "messages": [
            response
        ]
    }


# =========================================================
# ROUTER AFTER LLM
# =========================================================

def route_after_llm(
    state: AgentState,
) -> Literal[
    "tools",
    "inspect_response",
]:
    """
    Haddii model-ku tool call leeyahay -> tools.
    Haddii kale -> inspect_response.
    """

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

    return "inspect_response"


# =========================================================
# TOOL NODE
# =========================================================

tool_node = ToolNode(
    tools
)


# =========================================================
# RESPONSE INSPECTION NODE
# =========================================================

def inspect_response_node(
    state: AgentState,
) -> dict:
    """
    Hubi haddii LLM-ku soo saaray DRAFT_REQUEST.
    """

    last_message = state[
        "messages"
    ][-1]

    content = (
        last_message.content
        if hasattr(last_message, "content")
        else ""
    )

    if not isinstance(content, str):
        return {
            "draft_requested": False,
        }

    if "DRAFT_REQUEST" not in content:
        return {
            "draft_requested": False,
        }

    try:
        draft_section = content.split(
            "DRAFT_REQUEST",
            1,
        )[1]

        draft_section = draft_section.split(
            "END_DRAFT",
            1,
        )[0]

        lines = draft_section.strip().splitlines()

        to_email = ""
        subject = ""
        body_lines = []

        reading_body = False

        for line in lines:

            if line.startswith("TO:"):
                to_email = line.replace(
                    "TO:",
                    "",
                    1,
                ).strip()

                continue

            if line.startswith("SUBJECT:"):
                subject = line.replace(
                    "SUBJECT:",
                    "",
                    1,
                ).strip()

                continue

            if line.startswith("BODY:"):
                reading_body = True
                continue

            if reading_body:
                body_lines.append(
                    line
                )

        body = "\n".join(
            body_lines
        ).strip()

        if not to_email:
            return {
                "draft_requested": False,
                "error": (
                    "Draft recipient lama helin."
                ),
            }

        if not subject:
            return {
                "draft_requested": False,
                "error": (
                    "Draft subject lama helin."
                ),
            }

        if not body:
            return {
                "draft_requested": False,
                "error": (
                    "Draft body lama helin."
                ),
            }

        return {
            "pending_draft_to": to_email,
            "pending_draft_subject": subject,
            "pending_draft_body": body,
            "draft_requested": True,
            "error": "",
        }

    except Exception as error:

        return {
            "draft_requested": False,
            "error": (
                f"Draft parsing error: {error}"
            ),
        }


# =========================================================
# ROUTER AFTER RESPONSE INSPECTION
# =========================================================

def route_after_inspection(
    state: AgentState,
) -> Literal[
    "approval",
    "error_handler",
    "end",
]:
    """
    Draft request jiro -> approval.
    Error jiro -> error handler.
    Haddii kale -> END.
    """

    if state.get("error"):
        return "error_handler"

    if state.get(
        "draft_requested",
        False,
    ):
        return "approval"

    return "end"


# =========================================================
# HUMAN APPROVAL NODE
# =========================================================

def approval_node(
    state: AgentState,
) -> dict:
    """
    User-ka tus draft-ka ka hor save action.
    """

    print(
        "\n========================================"
    )

    print(
        "📧 Gmail Draft Preview\n"
    )

    print(
        f"To: {state['pending_draft_to']}"
    )

    print(
        f"Subject: {state['pending_draft_subject']}"
    )

    print(
        "\nBody:\n"
    )

    print(
        state["pending_draft_body"]
    )

    print(
        "\n========================================"
    )

    while True:

        answer = input(
            "\nMa kaydiyaa Gmail Drafts? "
            "(yes/no): "
        ).strip().lower()

        if answer in {
            "yes",
            "y",
            "haa",
            "h",
        }:

            return {
                "approved": True,
            }

        if answer in {
            "no",
            "n",
            "maya",
            "m",
        }:

            return {
                "approved": False,
            }

        print(
            "Fadlan qor yes ama no."
        )


# =========================================================
# ROUTER AFTER APPROVAL
# =========================================================

def route_after_approval(
    state: AgentState,
) -> Literal[
    "create_draft",
    "cancelled",
]:

    if state.get(
        "approved",
        False,
    ):
        return "create_draft"

    return "cancelled"


# =========================================================
# CREATE DRAFT NODE
# =========================================================

def create_draft_node(
    state: AgentState,
) -> dict:
    """
    Gmail Draft save action.

    EMAIL MA DIRAYO.
    """

    try:

        result = create_draft(
            state[
                "pending_draft_to"
            ],
            state[
                "pending_draft_subject"
            ],
            state[
                "pending_draft_body"
            ],
        )

        if (
            "error" in result.lower()
            and "status: draft only" not in result.lower()
        ):

            return {
                "error": result,
            }

        return {
            "draft_result": result,
            "error": "",
        }

    except Exception as error:

        return {
            "error": (
                f"Gmail draft error: {error}"
            ),
        }


# =========================================================
# ROUTER AFTER DRAFT
# =========================================================

def route_after_draft(
    state: AgentState,
) -> Literal[
    "draft_success",
    "error_handler",
]:

    if state.get("error"):
        return "error_handler"

    return "draft_success"


# =========================================================
# DRAFT SUCCESS NODE
# =========================================================

def draft_success_node(
    state: AgentState,
) -> dict:
    """
    Draft success message conversation-ka ku dar.
    """

    message = AIMessage(
        content=(
            "✅ Gmail draft-ka waa la kaydiyay.\n\n"
            f"To: {state['pending_draft_to']}\n"
            f"Subject: {state['pending_draft_subject']}\n\n"
            "Email-ka LAMA DIRIN."
        )
    )

    return {
        "messages": [
            message
        ],
        "draft_requested": False,
    }


# =========================================================
# CANCELLED NODE
# =========================================================

def cancelled_node(
    state: AgentState,
) -> dict:

    message = AIMessage(
        content=(
            "⛔ Draft-ka lama kaydin.\n"
            "Email-ka lama dirin."
        )
    )

    return {
        "messages": [
            message
        ],
        "draft_requested": False,
    }


# =========================================================
# ERROR HANDLER NODE
# =========================================================

def error_handler_node(
    state: AgentState,
) -> dict:

    error_message = (
        state.get("error")
        or "Khalad aan la garanayn ayaa dhacay."
    )

    message = AIMessage(
        content=(
            "❌ Hawsha lama dhammeystirin.\n\n"
            f"Sababta:\n{error_message}\n\n"
            "Wax Gmail action ah lama xaqiijin."
        )
    )

    return {
        "messages": [
            message
        ],
        "draft_requested": False,
    }


# =========================================================
# SQLITE PERSISTENT MEMORY
# =========================================================

connection = sqlite3.connect(
    "langgraph_memory.db",
    check_same_thread=False,
)

checkpointer = SqliteSaver(
    connection
)


# =========================================================
# BUILD GRAPH
# =========================================================

builder = StateGraph(
    AgentState
)


# =========================================================
# ADD NODES
# =========================================================

builder.add_node(
    "llm",
    llm_node,
)

builder.add_node(
    "tools",
    tool_node,
)

builder.add_node(
    "inspect_response",
    inspect_response_node,
)

builder.add_node(
    "approval",
    approval_node,
)

builder.add_node(
    "create_draft",
    create_draft_node,
)

builder.add_node(
    "draft_success",
    draft_success_node,
)

builder.add_node(
    "cancelled",
    cancelled_node,
)

builder.add_node(
    "error_handler",
    error_handler_node,
)


# =========================================================
# GRAPH EDGES
# =========================================================

builder.add_edge(
    START,
    "llm",
)


builder.add_conditional_edges(
    "llm",
    route_after_llm,
    {
        "tools": "tools",
        "inspect_response": "inspect_response",
    },
)


# Tool result dib ugu celi LLM
builder.add_edge(
    "tools",
    "llm",
)


builder.add_conditional_edges(
    "inspect_response",
    route_after_inspection,
    {
        "approval": "approval",
        "error_handler": "error_handler",
        "end": END,
    },
)


builder.add_conditional_edges(
    "approval",
    route_after_approval,
    {
        "create_draft": "create_draft",
        "cancelled": "cancelled",
    },
)


builder.add_conditional_edges(
    "create_draft",
    route_after_draft,
    {
        "draft_success": "draft_success",
        "error_handler": "error_handler",
    },
)


builder.add_edge(
    "draft_success",
    END,
)

builder.add_edge(
    "cancelled",
    END,
)

builder.add_edge(
    "error_handler",
    END,
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

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=user_message
                )
            ],

            "pending_draft_to": "",
            "pending_draft_subject": "",
            "pending_draft_body": "",

            "draft_requested": False,
            "approved": False,

            "draft_result": "",
            "error": "",
        },
        config=get_config(
            thread_id
        ),
    )

    final_message = result[
        "messages"
    ][-1]

    return final_message.content


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    print(
        "🤖 Final LangGraph Agent waa diyaar!"
    )

    print()

    print("Capabilities:")
    print("  Calculator")
    print("  Current Time")
    print("  Weather")
    print("  Gmail Recent")
    print("  Gmail Search")
    print("  Gmail Read")
    print("  Gmail Draft + Human Approval")
    print("  Persistent Conversation Memory")

    print()

    print("Commands:")
    print("  exit         -> ka bax")
    print(
        "  /thread NAME -> beddel conversation thread"
    )

    print()

    current_thread = "lesson23-final"

    while True:

        user_message = input(
            f"[{current_thread}] Adiga: "
        ).strip()

        # -------------------------------------------------
        # EXIT
        # -------------------------------------------------

        if user_message.lower() == "exit":

            print(
                "Nabadgelyo!"
            )

            connection.close()

            break

        # -------------------------------------------------
        # THREAD SWITCH
        # -------------------------------------------------

        if user_message.lower().startswith(
            "/thread "
        ):

            new_thread = user_message[
                len("/thread "):
            ].strip()

            if not new_thread:

                print(
                    "Fadlan thread name qor.\n"
                )

                continue

            current_thread = new_thread

            print(
                f"🧵 Thread-ka cusub: "
                f"{current_thread}\n"
            )

            continue

        # -------------------------------------------------
        # EMPTY INPUT
        # -------------------------------------------------

        if not user_message:

            print(
                "Fadlan wax qor.\n"
            )

            continue

        # -------------------------------------------------
        # RUN GRAPH
        # -------------------------------------------------

        try:

            answer = ask_agent(
                user_message,
                current_thread,
            )

            print(
                f"\nAgent: {answer}\n"
            )

        except KeyboardInterrupt:

            print(
                "\nOperation-ka waa la joojiyay.\n"
            )

        except Exception as error:

            print(
                f"\nKhalad: {error}\n"
            )


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":
    main()