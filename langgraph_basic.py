from app.agents.agent import (
    close_agent,
)

from app.services.agent_service import (
    chat_with_agent,
)


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    print(
        "🤖 Modular AI Agent waa diyaar!"
    )

    print()

    print("Commands:")
    print("  exit         -> ka bax")
    print(
        "  /thread NAME -> beddel conversation thread"
    )

    print()

    current_thread = (
        "lesson25-modular"
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

            close_agent()

            break

        # ---------------------------------------------
        # THREAD
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

            response = chat_with_agent(
    message=user_message,
    thread_id=current_thread,
)

if response.success:

    print(
        f"\nAgent:\n\n{response.answer}\n"
    )

else:

    print(
        f"\n❌ Error:\n{response.error}\n"
    )

        except KeyboardInterrupt:

            print(
                "\nOperation-ka waa la joojiyay.\n"
            )

        except Exception as error:

            print(
                f"\n❌ Agent Error: {error}\n"
            )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()