import json
from openai import OpenAI

from tools.calculator import calculator
from tools.time_tool import current_time
from tools.random_tool import random_number

client = OpenAI()

tools = [
    {
        "type": "function",
        "name": "calculator",
        "description": "Calculate a mathematical expression.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "type": "function",
        "name": "current_time",
        "description": "Return the current time.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "type": "function",
        "name": "random_number",
        "description": "Generate a random number.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]

while True:

    user = input("Adiga: ").strip()

    if user.lower() == "exit":
        break

    if not user:
        print("Fadlan wax qor.\n")
        continue

    response = client.responses.create(
        model="gpt-5.1",
        input=user,
        tools=tools
    )

    tool_used = False

    for item in response.output:

        if item.type != "function_call":
            continue

        tool_used = True

        arguments = json.loads(item.arguments)

        if item.name == "calculator":
            result = calculator(arguments["expression"])

        elif item.name == "current_time":
            result = current_time()

        elif item.name == "random_number":
            result = random_number()

        else:
            result = "Unknown tool"

        print(f"\n🔧 Tool ({item.name}): {result}")

    if not tool_used:
        print("\nAgent:", response.output_text)