# test_openrouter.py
import os
import asyncio
from dotenv import load_dotenv
import openai

load_dotenv()
client = openai.AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

async def test():
    try:
        response = await client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": "Скажи 'Привет'"}],
            max_tokens=10
        )
        print(" ураааа:", response.choices[0].message.content)
    except Exception as e:
        print("Твоя жизнь ошибка:", e)

asyncio.run(test())