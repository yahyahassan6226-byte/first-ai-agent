import json

from openai import OpenAI

from tools.calculator import calculator
from tools.random_tool import random_number
from tools.time_tool import current_time
from tools.weather_tool import get_weather


client = OpenAI()


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
            "Get the current weather for a city. Use this when the user "
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
]


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Fulinta tool-ka uu GPT doortay."""

    if tool_name == "calculator":
        return calculator(arguments["expression"])

    if tool_name == "current_time":
        return current_time()

    if tool_name == "random_number":
        return random_number()

    if tool_name == "get_weather":
        return get_weather(arguments["city"])

    return f"Error: Tool aan la aqoon: {tool_name}"


def ask_agent(user_message: str) -> str:
    """User-ka u dir GPT, fuli tool-ka, kadibna keen jawaabta ugu dambaysa."""

    conversation = [
        {
            "role": "user",
            "content": user_message,
        }
    ]

    response = client.responses.create(
        model="gpt-5.1",
        instructions=(
            "You are a helpful AI assistant. "
            "Use the available tools when they are needed. "
            "Respond clearly in the same language as the user."
        ),
        input=conversation,
        tools=tools,
    )

    conversation.extend(response.output)
    tool_called = False

    for item in response.output:
        if item.type != "function_call":
            continue

        tool_called = True

        try:
            arguments = json.loads(item.arguments)
            result = execute_tool(item.name, arguments)

        except (json.JSONDecodeError, KeyError, TypeError) as error:
            result = f"Tool error: {error}"

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

    if not tool_called:
        return response.output_text

    final_response = client.responses.create(
        model="gpt-5.1",
        instructions=(
            "Use the tool result to answer the user clearly. "
            "Respond in the same language as the user."
        ),
        input=conversation,
        tools=tools,
    )

    return final_response.output_text


def main() -> None:
    print("🤖 AI Agent waa diyaar!")
    print("Qor 'exit' si aad uga baxdo.\n")

    while True:
        user_message = input("Adiga: ").strip()

        if user_message.lower() == "exit":
            print("Nabadgelyo!")
            break

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