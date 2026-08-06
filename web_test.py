from openai import OpenAI


client = OpenAI()


response = client.responses.create(
    model="gpt-5.5",
    tools=[
        {
            "type": "web_search",
        }
    ],
    input="What is the latest important AI news today?",
)


print(response.output_text)