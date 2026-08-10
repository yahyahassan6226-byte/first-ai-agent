from agent import ask_agent, clear_conversation


def main() -> None:
    print("🤖 AI Agent waa diyaar!")
    print("Commands:")
    print("  exit   -> ka bax")
    print("  /clear -> nadiifi conversation memory")
    print()

    while True:
        user_message = input("Adiga: ").strip()

        if user_message.lower() == "exit":
            print("Nabadgelyo!")
            break

        if user_message.lower() == "/clear":
            clear_conversation()
            print("🧹 Conversation memory waa la nadiifiyay.\n")
            continue

        if not user_message:
            print("Fadlan wax qor.\n")
            continue

        try:
            answer = ask_agent(user_message)
            print(f"\nAgent: {answer}\n")

        except KeyboardInterrupt:
            print("\nOperation-ka waa la joojiyay.\n")

        except Exception as error:
            print(f"\nKhalad: {error}\n")


if __name__ == "__main__":
    main()