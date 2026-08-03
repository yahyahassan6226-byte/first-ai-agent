from openai import OpenAI

client = OpenAI()


def ask_agent(user_message):
    response = client.responses.create(
        model="gpt-5.5",
        instructions="You are a helpful AI assistant.",
        input=user_message,
    )
    return response.output_text


def calculator(expression):
    try:
        return str(eval(expression))
    except Exception:
        return None


print("🤖 AI Agent waa diyaar!")
print("Qor 'exit' si aad uga baxdo.\n")

while True:
    user = input("Adiga: ").strip()

    if user.lower() == "exit":
        print("Nabadgelyo!")
        break

    if not user:
        print("Fadlan wax qor.\n")
        continue

    result = calculator(user)

    if result is not None:
        print(f"\n🧮 Calculator: {result}\n")
        continue

    try:
        answer = ask_agent(user)
        print(f"\nAgent: {answer}\n")
    except Exception as e:
        print(f"\nKhalad: {e}\n")