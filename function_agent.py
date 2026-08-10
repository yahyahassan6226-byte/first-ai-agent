import json

from openai import OpenAI

from tools.calculator import calculator

from tools.gmail_tool import (
    create_draft,
    list_recent_emails,
    read_email,
    search_emails,
)

from tools.memory_tool import (
    get_memory,
    list_memories,
    save_memory,
)

from tools.pdf_tool import read_pdf
from tools.random_tool import random_number
from tools.rag_tool import index_pdf, search_pdf
from tools.time_tool import current_time
from tools.weather_tool import get_weather


# =========================================================
# OPENAI CLIENT
# =========================================================

client = OpenAI()


# =========================================================
# SHORT-TERM CONVERSATION MEMORY
# =========================================================

conversation = []


# =========================================================
# TOOLS
# =========================================================

tools = [

    # -----------------------------------------------------
    # CALCULATOR
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "calculator",
        "description": (
            "Calculate a mathematical expression accurately."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "Mathematical expression such as 25*30."
                    ),
                }
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # CURRENT TIME
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "current_time",
        "description": "Return the current local time.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # RANDOM NUMBER
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "random_number",
        "description": (
            "Generate a random number between 1 and 100."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # WEATHER
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "get_weather",
        "description": (
            "Get the current weather for a city."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": (
                        "City name such as Mogadishu, SO."
                    ),
                }
            },
            "required": ["city"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # PDF READER
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "read_pdf",
        "description": (
            "Read the entire PDF from the local documents folder. "
            "Use when the user explicitly asks to read or "
            "summarize an entire PDF."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": (
                        "Exact PDF filename including .pdf."
                    ),
                }
            },
            "required": ["file_name"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # INDEX PDF
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "index_pdf",
        "description": (
            "Index a PDF into the local vector database "
            "for RAG search."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": (
                        "Exact PDF filename including .pdf."
                    ),
                }
            },
            "required": ["file_name"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # SEARCH PDF / RAG
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "search_pdf",
        "description": (
            "Search an indexed PDF using semantic RAG search."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": (
                        "Exact PDF filename including .pdf."
                    ),
                },
                "question": {
                    "type": "string",
                    "description": (
                        "Question to search for inside the PDF."
                    ),
                },
            },
            "required": [
                "file_name",
                "question",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # SAVE MEMORY
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "save_memory",
        "description": (
            "Save a stable user fact or preference. "
            "Use only when the user explicitly asks "
            "you to remember it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": (
                        "Memory key such as favorite_city."
                    ),
                },
                "value": {
                    "type": "string",
                    "description": (
                        "Value to remember."
                    ),
                },
            },
            "required": [
                "key",
                "value",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # GET MEMORY
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "get_memory",
        "description": (
            "Retrieve a saved memory using its key."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": (
                        "Memory key."
                    ),
                }
            },
            "required": ["key"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # LIST MEMORIES
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "list_memories",
        "description": (
            "List all saved memories from SQLite."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # GMAIL: RECENT EMAILS
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "list_recent_emails",
        "description": (
            "List the user's most recent Gmail messages."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": (
                        "Number of emails to retrieve."
                    ),
                }
            },
            "required": ["max_results"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # GMAIL: SEARCH EMAILS
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "search_emails",
        "description": (
            "Search Gmail by sender, subject, keyword, "
            "date, unread status, or Gmail search syntax."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Gmail search query such as "
                        "from:google.com, is:unread, "
                        "subject:security or newer_than:7d."
                    ),
                },
                "max_results": {
                    "type": "integer",
                    "description": (
                        "Maximum number of results."
                    ),
                },
            },
            "required": [
                "query",
                "max_results",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # GMAIL: READ EMAIL
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "read_email",
        "description": (
            "Read a specific Gmail message using its Message ID. "
            "Use before summarizing or replying to a specific email."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": (
                        "Gmail Message ID."
                    ),
                }
            },
            "required": ["message_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # GMAIL: CREATE DRAFT
    # -----------------------------------------------------

    {
        "type": "function",
        "name": "create_draft",
        "description": (
            "Create and save an email draft in Gmail. "
            "This tool does NOT send the email. "
            "Use it only when the user explicitly asks "
            "to create or save a Gmail draft."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "to_email": {
                    "type": "string",
                    "description": (
                        "Recipient email address."
                    ),
                },
                "subject": {
                    "type": "string",
                    "description": (
                        "Draft email subject."
                    ),
                },
                "body": {
                    "type": "string",
                    "description": (
                        "Draft email body."
                    ),
                },
            },
            "required": [
                "to_email",
                "subject",
                "body",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # -----------------------------------------------------
    # WEB SEARCH
    # -----------------------------------------------------

    {
        "type": "web_search",
    },
]


# =========================================================
# EXECUTE CUSTOM TOOL
# =========================================================

def execute_tool(
    tool_name: str,
    arguments: dict,
) -> str:
    """Fulinta custom Python tools."""

    if tool_name == "calculator":
        return calculator(
            arguments["expression"]
        )

    if tool_name == "current_time":
        return current_time()

    if tool_name == "random_number":
        return random_number()

    if tool_name == "get_weather":
        return get_weather(
            arguments["city"]
        )

    if tool_name == "read_pdf":
        return read_pdf(
            arguments["file_name"]
        )

    if tool_name == "index_pdf":
        return index_pdf(
            arguments["file_name"]
        )

    if tool_name == "search_pdf":
        return search_pdf(
            arguments["file_name"],
            arguments["question"],
        )

    if tool_name == "save_memory":
        return save_memory(
            arguments["key"],
            arguments["value"],
        )

    if tool_name == "get_memory":
        return get_memory(
            arguments["key"]
        )

    if tool_name == "list_memories":
        return list_memories()

    if tool_name == "list_recent_emails":
        return list_recent_emails(
            arguments["max_results"]
        )

    if tool_name == "search_emails":
        return search_emails(
            arguments["query"],
            arguments["max_results"],
        )

    if tool_name == "read_email":
        return read_email(
            arguments["message_id"]
        )

    if tool_name == "create_draft":
        return create_draft(
            arguments["to_email"],
            arguments["subject"],
            arguments["body"],
        )

    return (
        f"Error: Tool aan la aqoon: {tool_name}"
    )


# =========================================================
# AGENT INSTRUCTIONS
# =========================================================

AGENT_INSTRUCTIONS = """
You are a helpful AI assistant.

Use conversation history to understand follow-up questions.

Use the available tools when appropriate.

LANGUAGE:
Respond in the same language as the user.

GMAIL:
Use list_recent_emails when the user asks for recent
or latest emails.

Use search_emails when the user asks to search Gmail
by sender, subject, keyword, date, unread status,
or another Gmail filter.

Translate natural-language Gmail searches into
appropriate Gmail search syntax.

Use read_email when the user asks to read a specific
email and its Message ID is available.

If the user asks to summarize a specific email,
read the email first if necessary.

Summaries must be based only on the Gmail content
returned by the tool.

A useful email summary may include:
- sender
- subject
- main point
- important details
- deadlines
- actions required

If the user asks you to WRITE a reply, you may generate
the proposed reply as text without saving anything to Gmail.

If the user only asks:
"write a reply",
"prepare a reply",
or similar wording,
DO NOT automatically create a Gmail draft.

Use create_draft only when the user explicitly asks
to CREATE or SAVE the draft in Gmail.

Examples that permit create_draft:
"Save this as a Gmail draft."
"Create a Gmail draft."
"Draft-kan Gmail ii geli."
"Draft Gmail ii samee."

Creating a Gmail draft is NOT the same as sending an email.

After create_draft succeeds, clearly tell the user
that the draft was saved but NOT SENT.

There is NO send-email tool.

Never claim that an email was sent.

Never invent email senders, subjects, recipients,
message IDs, dates, or email contents.

PDF / RAG:
Use read_pdf when the user asks to read or summarize
an entire PDF.

Use index_pdf when the user asks to index a PDF.

Use search_pdf for specific questions about an
indexed PDF.

For PDF questions, use only retrieved or extracted
PDF content.

If the information is not present in the PDF,
say so clearly.

MEMORY:
Use save_memory only when the user explicitly asks
you to remember a stable fact or preference.

Use get_memory or list_memories when the user asks
about something that may have been saved previously.

Never save passwords, API keys, OAuth tokens,
credentials, or other secrets.

WEB:
Use web search when the user requests current,
recent, latest, today's, news-related,
or internet-based information.

Do not invent missing information.
"""


# =========================================================
# RUN MODEL + TOOLS
# =========================================================

def run_agent_turn() -> str:
    """
    Run model/tool loop until the model returns
    a normal final answer.
    """

    while True:

        response = client.responses.create(
            model="gpt-5.1",
            instructions=AGENT_INSTRUCTIONS,
            input=conversation,
            tools=tools,
            tool_choice="auto",
        )

        conversation.extend(
            response.output
        )

        function_calls = []

        # Web Search waxaa fulinaya OpenAI
        for item in response.output:

            if item.type == "web_search_call":
                print(
                    "\n🌐 Web Search ayaa la isticmaalay."
                )

            if item.type == "function_call":
                function_calls.append(item)

        # Haddii custom tool call uusan jirin,
        # model-ku jawaabtiisa final ayuu keenay.
        if not function_calls:
            return response.output_text

        # Fulinta dhammaan custom tool calls
        for item in function_calls:

            try:
                arguments = json.loads(
                    item.arguments
                )

                result = execute_tool(
                    item.name,
                    arguments,
                )

            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as error:

                result = (
                    f"Tool error: {error}"
                )

            except Exception as error:

                result = (
                    f"Tool execution error: {error}"
                )

            print(
                f"\n🔧 Tool: {item.name}"
            )

            print(
                f"📥 Arguments: {item.arguments}"
            )

            print(
                f"📤 Result: {result}"
            )

            conversation.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": str(result),
                }
            )


# =========================================================
# ASK AGENT
# =========================================================

def ask_agent(
    user_message: str,
) -> str:
    """User message geli conversation-ka kadib agent-ka orod."""

    conversation.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    return run_agent_turn()


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    print("🤖 AI Agent waa diyaar!")

    print("Commands:")
    print("  exit   -> ka bax")
    print(
        "  /clear -> nadiifi conversation memory"
    )

    print()

    while True:

        user_message = input(
            "Adiga: "
        ).strip()

        if user_message.lower() == "exit":
            print("Nabadgelyo!")
            break

        if user_message.lower() == "/clear":

            conversation.clear()

            print(
                "🧹 Conversation memory "
                "waa la nadiifiyay.\n"
            )

            continue

        if not user_message:

            print(
                "Fadlan wax qor.\n"
            )

            continue

        try:

            answer = ask_agent(
                user_message
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
# START
# =========================================================

if __name__ == "__main__":
    main()