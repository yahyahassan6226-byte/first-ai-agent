import json

from openai import OpenAI

from tools.calculator import calculator
from tools.pdf_tool import read_pdf
from tools.random_tool import random_number
from tools.time_tool import current_time
from tools.weather_tool import get_weather
from tools.memory_tool import (
    save_memory,
    get_memory,
    list_memories,
)


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
            "Get the current weather for a city. Use this tool when the user "
            "asks about temperature, humidity, wind, or current conditions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": (
                        "City name, optionally with country code, "
                        "such as 'Mogadishu, SO'."
                    ),
                }
            },
            "required": ["city"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "read_pdf",
        "description": (
            "Read and extract text from a PDF file located in the local "
            "documents folder. Always use this tool when the user asks to "
            "read, summarize, inspect, or answer questions about a named PDF."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": (
                        "The exact PDF filename including .pdf, such as "
                        "'ROLE OF MARKETING STRATEGIES.pdf'."
                    ),
                }
            },
            "required": ["file_name"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "save_memory",
        "description": (
            "Save an important stable user fact or preference for future "
            "conversations. Use this when the user explicitly asks you "
            "to remember something."
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

    if tool_name == "save_memory":
        return save_memory(
            arguments["key"],
            arguments["value"],
        )

    if tool_name == "get_memory":
        return get_memory(
            arguments["key"],
        )

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
            "Use web search for current, recent, latest, today's, "
            "news-related, or internet-based information. "
            "When the user asks about a named PDF, use read_pdf. "
            "Answer PDF questions using only the extracted PDF content. "
            "If the PDF does not contain the answer, say so clearly. "
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

    # Save the model's first response/tool requests in conversation history
    conversation.extend(response.output)

    custom_tool_called = False

    # Hosted web search is executed by OpenAI
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

    # If no custom Python tool was called,
    # the final answer is already available.
    if not custom_tool_called:
        return response.output_text

    # Send custom tool results back to GPT
    final_response = client.responses.create(
        model="gpt-5.1",
        instructions=(
            "Use the tool result and conversation history to answer clearly. "
            "For PDF questions, rely only on the extracted PDF content. "
            "For memory questions, rely on the returned database result. "
            "Respond in the same language as the user."
        ),
        input=conversation,
        tools=tools,
        tool_choice="auto",
    )

    # Save final assistant answer in short-term conversation memory
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