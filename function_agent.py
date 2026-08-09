import json

from openai import OpenAI

from tools.calculator import calculator
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


client = OpenAI()

# Short-term conversation memory
conversation = []


tools = [
    {
        "type": "function",
        "name": "calculator",
        "description": "Calculate a mathematical expression accurately.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression, such as 25*30.",
                }
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
        "strict": True,
    },
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
    {
        "type": "function",
        "name": "random_number",
        "description": "Generate a random number between 1 and 100.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_weather",
        "description": (
            "Get the current weather for a city. "
            "Use this when the user asks about temperature, humidity, "
            "wind, or current weather conditions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": (
                        "City name, optionally including a country code, "
                        "such as 'Mogadishu, SO'."
                    ),
                }
            },
            "required": ["city"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # PDF full reader
    {
        "type": "function",
        "name": "read_pdf",
        "description": (
            "Read the entire PDF file from the local documents folder. "
            "Use this ONLY when the user explicitly asks to read, inspect, "
            "or summarize the whole PDF. "
            "Do NOT use this for specific questions about an indexed PDF. "
            "For specific PDF questions, use search_pdf instead."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "The exact PDF filename including .pdf.",
                }
            },
            "required": ["file_name"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # RAG indexing
    {
        "type": "function",
        "name": "index_pdf",
        "description": (
            "Index a PDF into the local ChromaDB vector database. "
            "Use this ONLY when the user asks to index, prepare, "
            "or add a PDF for RAG semantic search."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "The exact PDF filename including .pdf.",
                }
            },
            "required": ["file_name"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # RAG semantic search
    {
        "type": "function",
        "name": "search_pdf",
        "description": (
            "Search an indexed PDF using RAG semantic vector search. "
            "ALWAYS use this tool for specific questions about a PDF, "
            "such as asking for its title, author, objectives, methodology, "
            "findings, recommendations, conclusions, or any specific fact. "
            "Prefer this tool over read_pdf for specific PDF questions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "The exact PDF filename including .pdf.",
                },
                "question": {
                    "type": "string",
                    "description": "The user's exact question about the PDF.",
                },
            },
            "required": ["file_name", "question"],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # Long-term memory
    {
        "type": "function",
        "name": "save_memory",
        "description": (
            "Save an important stable user fact or preference for future "
            "conversations. Use this only when the user explicitly asks "
            "you to remember something."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Short memory key, such as favorite_language.",
                },
                "value": {
                    "type": "string",
                    "description": "The value to remember.",
                },
            },
            "required": ["key", "value"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_memory",
        "description": "Retrieve a previously saved memory by key.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The memory key to retrieve.",
                }
            },
            "required": ["key"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "list_memories",
        "description": "List all memories saved in the local SQLite database.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },

    # OpenAI hosted web search
    {
        "type": "web_search",
    },
]


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Fulinta custom Python tool-ka uu GPT doortay."""

    if tool_name == "calculator":
        return calculator(arguments["expression"])

    if tool_name == "current_time":
        return current_time()

    if tool_name == "random_number":
        return random_number()

    if tool_name == "get_weather":
        return get_weather(arguments["city"])

    if tool_name == "read_pdf":
        return read_pdf(arguments["file_name"])

    if tool_name == "index_pdf":
        return index_pdf(arguments["file_name"])

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
        return get_memory(arguments["key"])

    if tool_name == "list_memories":
        return list_memories()

    return f"Error: Tool aan la aqoon: {tool_name}"


def ask_agent(user_message: str) -> str:
    """U dir fariinta GPT iyadoo conversation history la ilaalinayo."""

    conversation.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    response = client.responses.create(
        model="gpt-5.1",
        instructions=(
            "You are a helpful AI assistant. "
            "Use conversation history to understand follow-up questions. "
            "Use the available tools whenever needed. "

            "PDF ROUTING RULES: "
            "If the user asks a SPECIFIC question about an indexed PDF, "
            "you MUST use search_pdf. "
            "Examples: title, author, objectives, methodology, findings, "
            "recommendations, conclusions, or any specific fact. "
            "Use read_pdf ONLY when the user explicitly asks to read "
            "or summarize the ENTIRE PDF. "
            "Use index_pdf ONLY when the user asks to index or prepare a PDF. "
            "For PDF answers, rely only on retrieved or extracted PDF content. "
            "If the retrieved PDF content does not contain the answer, "
            "say so clearly and do not invent information. "

            "Use web search for current, recent, latest, today's, "
            "news-related, or internet-based information. "

            "Use save_memory only when the user explicitly asks you to "
            "remember a stable fact or preference. "
            "Use get_memory or list_memories when the user asks about "
            "something that may have been saved previously. "
            "Never save passwords, API keys, authentication tokens, "
            "or other secrets. "

            "Respond in the same language as the user."
        ),
        input=conversation,
        tools=tools,
        tool_choice="auto",
    )

    # Kaydi response-ka hore
    conversation.extend(response.output)

    custom_tool_called = False

    # Hosted Web Search
    for item in response.output:
        if item.type == "web_search_call":
            print("\n🌐 Web Search ayaa la isticmaalay.")

    # Custom Python tools
    for item in response.output:
        if item.type != "function_call":
            continue

        custom_tool_called = True

        try:
            arguments = json.loads(item.arguments)
            result = execute_tool(item.name, arguments)

        except (json.JSONDecodeError, KeyError, TypeError) as error:
            result = f"Tool error: {error}"

        except Exception as error:
            result = f"Tool execution error: {error}"

        print(f"\n🔧 Tool: {item.name}")
        print(f"📥 Arguments: {item.arguments}")
        print(f"📤 Result: {result}")

        conversation.append(
            {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": result,
            }
        )

    # Haddii custom tool aan la isticmaalin
    if not custom_tool_called:
        return response.output_text

    # Tool result-ka dib ugu dir GPT
    final_response = client.responses.create(
        model="gpt-5.1",
        instructions=(
            "Use the tool result and conversation history to answer clearly. "
            "For RAG/PDF questions, answer ONLY from the retrieved PDF chunks "
            "or extracted PDF content. "
            "If the information is not present, say so clearly. "
            "For memory questions, rely on the returned database result. "
            "Respond in the same language as the user."
        ),
        input=conversation,
        tools=tools,
        tool_choice="auto",
    )

    conversation.extend(final_response.output)

    return final_response.output_text


def main() -> None:
    print("🤖 AI Agent waa diyaar!")
    print("Commands:")
    print("  exit   -> ka bax")
    print("  /clear -> nadiifi conversation memory\n")

    while True:
        user_message = input("Adiga: ").strip()

        if user_message.lower() == "exit":
            print("Nabadgelyo!")
            break

        if user_message.lower() == "/clear":
            conversation.clear()
            print("🧹 Conversation memory waa la nadiifiyay.\n")
            continue

        if not user_message:
            print("Fadlan wax qor.\n")
            continue

        try:
            answer = ask_agent(user_message)
            print(f"\nAgent: {answer}\n")

        except Exception as error:
            print(f"\nKhalad: {error}\n")


if __name__ == "__main__":
    main()