import json

from openai import OpenAI

from agent_tools import TOOLS, execute_tool
from config import MODEL, MAX_AGENT_STEPS
from prompts.system_prompt import SYSTEM_PROMPT


# =========================================================
# OPENAI CLIENT
# =========================================================

client = OpenAI()


# =========================================================
# SHORT-TERM CONVERSATION MEMORY
# =========================================================

conversation = []


# =========================================================
# TOOL ERROR FORMAT
# =========================================================

def format_tool_error(
    tool_name: str,
    error_type: str,
    message: str,
) -> str:
    """
    Tool error-ka u beddel format cad
    oo model-ku si fudud u fahmi karo.
    """

    return (
        "TOOL_ERROR\n"
        f"Tool: {tool_name}\n"
        f"Type: {error_type}\n"
        f"Message: {message}\n"
        "The requested action did not succeed."
    )


# =========================================================
# RUN ONE AGENT TURN
# =========================================================

def run_agent_turn() -> str:
    """
    Orod agent-ka ilaa uu ka keenayo jawaab final ah.

    MAX_AGENT_STEPS wuxuu ka ilaalinayaa agent-ka
    inuu galo tool loop aan dhammaanayn.
    """

    # Hal user turn gudaheed waxaan xasuusaneynaa
    # tool calls-kii isku argument-ka ahaa.
    previous_calls = set()

    for step in range(1, MAX_AGENT_STEPS + 1):

        # -------------------------------------------------
        # MODEL CALL
        # -------------------------------------------------

        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=conversation,
            tools=TOOLS,
            tool_choice="auto",
        )

        # Kaydi model output-ka conversation history
        conversation.extend(
            response.output
        )

        function_calls = []

        # -------------------------------------------------
        # INSPECT MODEL OUTPUT
        # -------------------------------------------------

        for item in response.output:

            # OpenAI hosted web search
            if item.type == "web_search_call":
                print(
                    "\n🌐 Web Search ayaa la isticmaalay."
                )

            # Custom Python tool
            if item.type == "function_call":
                function_calls.append(item)

        # -------------------------------------------------
        # FINAL ANSWER
        # -------------------------------------------------

        if not function_calls:
            return response.output_text

        print(
            f"\n🧠 Agent Step: "
            f"{step}/{MAX_AGENT_STEPS}"
        )

        # -------------------------------------------------
        # EXECUTE CUSTOM TOOLS
        # -------------------------------------------------

        for item in function_calls:

            tool_name = item.name
            raw_arguments = item.arguments

            try:

                # -----------------------------------------
                # PARSE ARGUMENTS
                # -----------------------------------------

                arguments = json.loads(
                    raw_arguments
                )

                # -----------------------------------------
                # REPEATED TOOL CALL PROTECTION
                # -----------------------------------------

                call_signature = (
                    tool_name,
                    raw_arguments,
                )

                if call_signature in previous_calls:

                    result = format_tool_error(
                        tool_name,
                        "RepeatedToolCall",
                        (
                            "The same tool call was already "
                            "attempted with identical arguments."
                        ),
                    )

                else:

                    previous_calls.add(
                        call_signature
                    )

                    # -------------------------------------
                    # EXECUTE TOOL
                    # -------------------------------------

                    result = execute_tool(
                        tool_name,
                        arguments,
                    )

            # ---------------------------------------------
            # JSON ERROR
            # ---------------------------------------------

            except json.JSONDecodeError as error:

                result = format_tool_error(
                    tool_name,
                    "JSONDecodeError",
                    str(error),
                )

            # ---------------------------------------------
            # MISSING ARGUMENT
            # ---------------------------------------------

            except KeyError as error:

                result = format_tool_error(
                    tool_name,
                    "MissingArgument",
                    (
                        "Missing required argument: "
                        f"{error}"
                    ),
                )

            # ---------------------------------------------
            # INVALID ARGUMENT TYPE / VALUE
            # ---------------------------------------------

            except (TypeError, ValueError) as error:

                result = format_tool_error(
                    tool_name,
                    "InvalidArgument",
                    str(error),
                )

            # ---------------------------------------------
            # FILE NOT FOUND
            # ---------------------------------------------

            except FileNotFoundError as error:

                result = format_tool_error(
                    tool_name,
                    "FileNotFound",
                    str(error),
                )

            # ---------------------------------------------
            # ALL OTHER TOOL ERRORS
            # ---------------------------------------------

            except Exception as error:

                result = format_tool_error(
                    tool_name,
                    type(error).__name__,
                    str(error),
                )

            # -------------------------------------------------
            # DEBUG OUTPUT
            # -------------------------------------------------

            print(
                f"\n🔧 Tool: {tool_name}"
            )

            print(
                f"📥 Arguments: {raw_arguments}"
            )

            print(
                f"📤 Result: {result}"
            )

            # -------------------------------------------------
            # RETURN TOOL RESULT TO MODEL
            # -------------------------------------------------

            conversation.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": str(result),
                }
            )

    # =====================================================
    # MAX STEP SAFETY STOP
    # =====================================================

    return (
        "Agent-ku wuxuu gaaray xadka "
        f"{MAX_AGENT_STEPS} tallaabo. "
        "Hawsha waa la joojiyay si looga "
        "hortago loop aan dhammaanayn."
    )


# =========================================================
# ASK AGENT
# =========================================================

def ask_agent(
    user_message: str,
) -> str:
    """
    User message-ka geli conversation history,
    kadibna orod agent-ka.
    """

    conversation.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    return run_agent_turn()


# =========================================================
# CLEAR SHORT-TERM MEMORY
# =========================================================

def clear_conversation() -> None:
    """
    Nadiifi short-term conversation memory.

    Tani ma tirtirayso SQLite long-term memory.
    """

    conversation.clear()


# =========================================================
# OPTIONAL DEBUG HELPERS
# =========================================================

def get_conversation_length() -> int:
    """
    Soo celi inta item ee conversation history ku jirta.
    """

    return len(conversation)


def get_conversation() -> list:
    """
    Soo celi conversation history-ga hadda jira.

    Waxaa loogu talagalay debugging.
    """

    return conversation.copy()