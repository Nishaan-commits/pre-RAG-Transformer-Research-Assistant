"""

Responsibility: Send a prompt to the Groq API and return the response text.

"""

import os
from groq import Groq
from dotenv import load_dotenv
from config import GROQ_MODEL

# load_dotenv() reads your .env file and puts variables into os.environ
load_dotenv()

_client = Groq(api_key = os.getenv("GROQ_API_KEY"))

def generate_answer(prompt: str, model:str = GROQ_MODEL) -> str:

    response = _client.chat.completions.create(
        model = model,
        messages = [
            {
                "role" : "user",
                "content" : prompt
            }
        ],
        temperature=0.2,
        max_tokens = 512
    )

    return response.choices[0].message.content.strip()