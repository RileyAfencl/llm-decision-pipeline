import pytest
pytest.skip("Manual import check; not part of unit test suite.", allow_module_level=True)
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import os


# Figure out where the .env file is
env_path = Path(__file__).with_name(".env")
print("Env path:", env_path)

# Load that .env file
loaded = load_dotenv(dotenv_path=env_path)
print("Dotenv loaded:", loaded)

# Check whether the key is visible to Python
print("Key present:", os.getenv("OPENAI_API_KEY") is not None)

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Hello, what can you do?"}
    ]
)

print(response.choices[0].message.content)