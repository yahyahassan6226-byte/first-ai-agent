import sqlite3

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver

from config import MODEL

from langchain_tools import (
    calculator,
    create_draft,
    current_time,
    get_weather,
    list_recent_emails,
    read_email,
    search_emails,
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
    calculator,
    current_time,
    get_weather,
    list_recent_emails,
    search_emails,
    read_email,
    create_draft,
]


# =========================================================
# SQLITE PERSISTENT MEMORY
# =========================================================

connection = sqlite3.connect(
    "langchain_memory.db",
    check_same_thread=False,
)

checkpointer = SqliteSaver(
    connection
)


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are a helpful multi-step AI assistant.

Respond clearly in the same language as the user.

Use conversation history to understand follow-up questions.

You may use multiple tools sequentially when necessary.

Do not stop after the first tool call if another tool
is required to complete the user's request.

Use tool results accurately.

Never invent a tool result.


CALCULATOR:

Use calculator whenever the user asks for
a mathematical calculation.


TIME:

Use current_time whenever the user asks for
the current local date or time.

Do not invent the current time or date if the tool
is available and the user explicitly asks for it.


WEATHER:

Use get_weather whenever the user asks for
current weather, temperature, humidity,
wind, or weather conditions.

Never invent current weather.


GMAIL RECENT EMAILS:

Use list_recent_emails when the user asks
for recent or latest Gmail messages.


GMAIL SEARCH:

Use search_emails when the user asks to find
emails by sender, subject, keyword, date,
unread status, or another Gmail filter.

Translate natural-language searches into
appropriate Gmail search queries.


GMAIL READ:

If search_emails returns a Message ID and
the user asks to read, summarize, analyze,
or reply to that email, use read_email.

Do not invent email contents.


EMAIL SUMMARIZATION:

When summarizing an email, rely only on
the content returned by Gmail tools.

If information is not in the returned email,
do not invent it.


EMAIL REPLIES:

If the user asks you to write or prepare a reply,
you may generate the reply as text.

Generating reply text does NOT automatically mean
saving anything to Gmail.


GMAIL DRAFTS:

Use create_draft only when the user explicitly asks
to create or save a Gmail draft.

Creating a draft is NOT sending an email.

After create_draft succeeds, clearly state that
the draft was saved but NOT SENT.

There is no send-email tool available.

Never claim that an email was sent.


ERROR RECOVERY:

Tool results may contain TOOL_ERROR.

If a tool returns TOOL_ERROR:

1. Do NOT claim that the requested action succeeded.

2. Read the error type and message carefully.

3. If another safe tool or reasonable alternative
   can solve the user's original request, you may
   use that alternative.

4. Do not repeatedly call the same failing tool
   with identical arguments.

5. If required information is missing, ask the user.

6. If the problem cannot be recovered from,
   explain the failure clearly.

7. Never invent a successful tool result.

8. Never hide the fact that the tool failed.


GENERAL SAFETY:

Use only tools necessary for the request.

Do not perform Gmail draft actions unless the user
explicitly asks for them.

Never claim to have sent an email.

Only give a final answer after the user's complete
request has been handled.
"""


# =========================================================
# CREATE AGENT
# =========================================================

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)


# =========================================================
# THREAD CONFIG
# =========================================================

def get_config(
    thread_id: str,
) -> dict:
    """
    Thread kasta wuxuu leeyahay persistent state gaar ah.
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
    User message u dir LangChain Agent-ka.
    """

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                }
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

    return final_message.content


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    print(
        "🤖 LangChain Safe Multi-Tool Agent waa diyaar!"
    )

    print()

    print("Tools:")
    print("  calculator")
    print("  current_time")
    print("  get_weather")
    print("  list_recent_emails")
    print("  search_emails")
    print("  read_email")
    print("  create_draft")

    print()

    print("Commands:")
    print("  exit         -> ka bax")
    print(
        "  /thread NAME -> beddel conversation thread"
    )

    print()

    current_thread = "safe-agent"

    print(
        f"Thread-ka hadda: {current_thread}\n"
    )

    while True:

        user_message = input(
            f"[{current_thread}] Adiga: "
        ).strip()

        # ---------------------------------------------
        # EXIT
        # ---------------------------------------------

        if user_message.lower() == "exit":

            print(
                "Nabadgelyo!"
            )

            connection.close()

            break

        # ---------------------------------------------
        # THREAD SWITCH
        # ---------------------------------------------

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

        # ---------------------------------------------
        # EMPTY INPUT
        # ---------------------------------------------

        if not user_message:

            print(
                "Fadlan wax qor.\n"
            )

            continue

        # ---------------------------------------------
        # RUN AGENT
        # ---------------------------------------------

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
                "\nKhalad weyn ayaa dhacay: "
                f"{error}\n"
            )


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":
    main()