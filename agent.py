import json

from openai import OpenAI

from agent_tools import TOOLS, execute_tool
from config import MODEL
from prompts.system_prompt import SYSTEM_PROMPT


client = OpenAI()


# Short-term conversation memory
conversation = []


def run_agent_turn() -> str:
    """
    Orod agent-ka ilaa uu ka keenayo jawaab final ah.
    """

    while True:

        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=conversation,
            tools=TOOLS,
            tool_choice="auto",
        )

        conversation.extend(response.output)

        function_calls = []

        # Hosted web search detection
        for item in response.output:

            if item.type == "web_search_call":
                print("\n🌐 Web Search ayaa la isticmaalay.")

            if item.type == "function_call":
                function_calls.append(item)

        # Haddii custom tool call jirin,
        # model-ku wuxuu keenay jawaab final ah.
        if not function_calls:
            return response.output_text

        # Fulinta custom tools
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
                    "output": str(result),
                }
            )


def ask_agent(user_message: str) -> str:
    """
    User message geli conversation-ka kadib agent-ka orod.
    """

    conversation.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    return run_agent_turn()


def clear_conversation() -> None:
    """
    Nadiifi short-term conversation memory.
    """

    conversation.clear()