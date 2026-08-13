import sqlite3
from typing import Annotated, TypedDict

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import (
    END,
    START,
    StateGraph,
)
from langgraph.graph.message import add_messages
from langgraph.prebuilt import (
    ToolNode,
    tools_condition,
)
from langgraph.types import RetryPolicy

from config import MODEL

from langchain_tools import (
    calculator,
    current_time,
    get_weather,
    list_recent_emails,
    read_email,
    search_emails,
)

from tools.rag_tool import (
    search_documents,
)


# =========================================================
# MODEL
# =========================================================

model = ChatOpenAI(
    model=MODEL,
)


# =========================================================
# TOOLS
# =========================================================

tools = [
    search_documents,
    calculator,
    current_time,
    get_weather,
    list_recent_emails,
    search_emails,
    read_email,
]


# =========================================================
# MODEL + TOOLS
# =========================================================

model_with_tools = model.bind_tools(
    tools
)


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are a reliable multi-step RAG AI assistant.

Respond clearly in the same language as the user.

Use conversation history to understand follow-up questions.

You may use one or multiple tools when necessary.


============================================================
RAG / LOCAL DOCUMENTS
============================================================

Use search_documents when the user's request depends on
information from local indexed PDFs or documents.

Examples:

- What does the personal development guide say about goals?
- According to the marketing strategies PDF...
- Summarize what the document says about communication.
- Compare two ideas discussed in the indexed documents.

Do NOT use RAG only because the topic happens to exist
in a document.

Example:

"What is personal development?"
-> answer normally

"What does the personal development guide say about
personal development?"
-> use search_documents


============================================================
FOLLOW-UP DOCUMENT QUESTIONS
============================================================

Use conversation history to resolve references such as:

- it
- that
- this
- the previous point
- that section
- the document
- there

When calling search_documents, pass a clear standalone question.

Example:

Previous user question:
"What does the personal development guide say about goal setting?"

Follow-up:
"Why is that important?"

Good RAG tool input:

"Why is goal setting important according to the
personal development guide?"

Do not send an ambiguous query such as:

"Why is that important?"


============================================================
RAG SOURCES
============================================================

search_documents may return verified source file names
and page numbers.

Preserve those sources when relevant.

Never invent source names or page numbers.

Never claim that information came from a PDF unless
the RAG tool actually returned supporting information.


============================================================
MULTI-STEP RAG
============================================================

You may call search_documents multiple times.

Example:

User:
"Compare what the document says about customer retention
and customer acquisition."

Possible workflow:

1. search_documents about customer retention
2. search_documents about customer acquisition
3. compare retrieved results
4. final answer


You may combine RAG with another tool.

Example:

User:
"Find the percentage mentioned in the document and
calculate that percentage of 500."

Possible workflow:

1. search_documents
2. extract supported percentage
3. calculator
4. final answer

Never invent a numeric value if the document did not
provide one.


============================================================
CALCULATOR
============================================================

Use calculator for mathematical calculations.

Use the calculator result accurately.


============================================================
CURRENT TIME
============================================================

Use current_time whenever the user explicitly asks
for the current local date or time.

Do not guess current time.


============================================================
WEATHER
============================================================

Use get_weather for current weather information,
including:

- temperature
- humidity
- wind
- current conditions

Use conversation history to resolve locations in
follow-up questions when possible.


============================================================
GMAIL
============================================================

Use list_recent_emails when the user asks for
latest or recent Gmail messages.

Use search_emails when the user asks to locate emails
by sender, subject, keyword, date, or Gmail search filter.

Use read_email when the user asks to read, summarize,
or analyze a specific email.

For a request such as:

"Find the latest email from Zapier and summarize it."

Possible workflow:

1. search_emails
2. obtain Message ID
3. read_email
4. summarize
5. final answer


============================================================
RAG ERRORS
============================================================

search_documents may return RAG_ERROR.

If you receive RAG_ERROR:

1. Do not claim retrieval succeeded.
2. Do not invent document content.
3. Explain that document retrieval failed.
4. If the question specifically depends on local documents,
   say the answer cannot currently be verified.
5. Do not repeatedly call search_documents with identical
   arguments after the same failure.


============================================================
GENERAL TOOL ERRORS
============================================================

Never invent tool results.

Never claim a failed operation succeeded.

Do not repeatedly call the same failing tool with
identical arguments.

If required information is missing, ask the user.

If the requested task cannot be completed, clearly
explain why.


============================================================
GMAIL SAFETY
============================================================

There is no email sending tool available.

Never claim an email was sent.

Do not invent Gmail messages or Gmail action results.


============================================================
FINAL ANSWER
============================================================

Only provide a confident final answer after all required
tool calls have completed.

For document-based answers, preserve verified sources.

For general questions that do not require tools,
answer directly.
"""


# =========================================================
# GRAPH STATE
# =========================================================

class AgentState(TypedDict):
    """
    messages field-ku wuxuu isticmaalaa add_messages reducer,
    sidaas darteed messages cusub waxaa lagu daraa history-ga.
    """

    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]


# =========================================================
# LLM NODE
# =========================================================

def llm_node(
    state: AgentState,
) -> dict:
    """
    Conversation history-ga oo dhan u dir model-ka.
    """

    response = model_with_tools.invoke(
        [
            SystemMessage(
                content=SYSTEM_PROMPT
            ),
            *state["messages"],
        ]
    )

    return {
        "messages": [
            response
        ]
    }


# =========================================================
# TOOL NODE
# =========================================================

tool_node = ToolNode(
    tools
)


# =========================================================
# RETRY POLICY
# =========================================================

llm_retry_policy = RetryPolicy(
    initial_interval=1.0,
    backoff_factor=2.0,
    max_interval=8.0,
    max_attempts=3,
    jitter=True,
)


# =========================================================
# SQLITE PERSISTENT MEMORY
# =========================================================

connection = sqlite3.connect(
    "rag_agent_memory.db",
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
    retry_policy=llm_retry_policy,
)

builder.add_node(
    "tools",
    tool_node,
)


# =========================================================
# START
# =========================================================

builder.add_edge(
    START,
    "llm",
)


# =========================================================
# CONDITIONAL TOOL ROUTING
# =========================================================

builder.add_conditional_edges(
    "llm",
    tools_condition,
    {
        "tools": "tools",
        "__end__": END,
    },
)


# =========================================================
# TOOL -> LLM LOOP
# =========================================================

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
    """
    Thread kasta wuxuu leeyahay conversation state gaar ah.
    """

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
    """
    User message u dir Final RAG Agent-ka.
    """

    user_message = user_message.strip()

    if not user_message:

        raise ValueError(
            "Message-ku madhan ma noqon karo."
        )

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

        return (
            "Agent-ku jawaab ma soo saarin."
        )

    final_message = messages[-1]

    return str(
        final_message.content
    )


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    print(
        "🤖 FINAL RAG AGENT waa diyaar!"
    )

    print()

    print("Capabilities:")
    print("  ✅ RAG document search")
    print("  ✅ Verified PDF sources")
    print("  ✅ Multi-step RAG")
    print("  ✅ Calculator")
    print("  ✅ Current time")
    print("  ✅ Weather")
    print("  ✅ Gmail recent")
    print("  ✅ Gmail search")
    print("  ✅ Gmail read")
    print("  ✅ Persistent conversation memory")
    print("  ✅ Tool error recovery")
    print("  ✅ LLM retry policy")

    print()

    print("Commands:")
    print("  exit         -> ka bax")
    print(
        "  /thread NAME -> beddel conversation thread"
    )

    print()

    current_thread = (
        "lesson24-final-rag"
    )

    print(
        f"Thread-ka hadda: "
        f"{current_thread}\n"
    )

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
        # EMPTY MESSAGE
        # -------------------------------------------------

        if not user_message:

            print(
                "Fadlan wax qor.\n"
            )

            continue

        # -------------------------------------------------
        # RUN FINAL AGENT
        # -------------------------------------------------

        try:

            answer = ask_agent(
                user_message,
                current_thread,
            )

            print(
                f"\nAgent:\n\n{answer}\n"
            )

        except KeyboardInterrupt:

            print(
                "\nOperation-ka waa la joojiyay.\n"
            )

        except Exception as error:

            print(
                "\n❌ Final RAG Agent Error:\n"
                f"{type(error).__name__}: {error}\n"
            )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()