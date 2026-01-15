from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
env_path = Path(__file__).with_name(".env")
load_dotenv(dotenv_path=env_path)

client = OpenAI()


def explain_concept(concept: str) -> str:
    messages = [
        {
            "role": "system",
            "content": "You are a concise technical assistant. Respond in bullet points only."
        },
        {
            "role": "user",
            "content": f"Explain this concept to a developer: {concept}"
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2
    )

    return response.choices[0].message.content
if __name__ == "__main__":
    topic = input("Enter a concept to explain: ")
    print(explain_concept(topic))