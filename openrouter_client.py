import json
import logging
import re
import asyncio
import openai
from config import OPENROUTER_API_KEY

logger = logging.getLogger(__name__)

client = openai.AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://t.me/your_bot",
        "X-Title": "Teacher Bot",
    }
)

async def generate_test(subject: str, difficulty: str, num_questions: int, max_retries=7) -> list:
    prompt = f"""Составь тест по предмету "{subject}" (уровень сложности: {difficulty}) из {num_questions} вопросов.
Все вопросы, варианты ответов и пояснения должны быть на русском языке.
Формат ответа строго JSON: список объектов, каждый с полями:
- question: текст вопроса
- options: список из 4 строк (варианты ответов)
- correct: индекс правильного ответа (0-3)
- explanation: краткое пояснение (1-2 предложения)

Пример:
[
  {{
    "question": "Сколько будет 2+2?",
    "options": ["3", "4", "5", "6"],
    "correct": 1,
    "explanation": "2+2=4"
  }}
]

Убедись, что JSON валидный и не содержит лишнего текста. Ответ должен содержать только JSON.
"""

    for attempt in range(max_retries):
        try:
            logger.info(f"Попытка {attempt+1}/{max_retries} для {subject}")
            response = await client.chat.completions.create(
                model="openrouter/free",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2500,
                timeout=30.0
            )
            content = response.choices[0].message.content
            if not content:
                logger.warning(f"Пустой ответ от модели (попытка {attempt+1})")
                await asyncio.sleep(2 ** attempt)
                continue

            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if not json_match:
                json_match = re.search(r'(\[[\s\S]*\])', content)
            json_str = json_match.group(1) if json_match else content
            json_str = json_str.strip()

            questions = json.loads(json_str)
            if isinstance(questions, list) and len(questions) > 0:
                logger.info(f"Успешно сгенерировано {len(questions)} вопросов для {subject}")
                return questions[:num_questions]
            else:
                logger.warning(f"Некорректный формат ответа: {type(questions)}")
        except Exception as e:
            logger.warning(f"Ошибка при генерации теста для {subject} (попытка {attempt+1}): {e}")
            if hasattr(e, 'status_code') and e.status_code == 429:
                wait = 2 ** attempt * 2
                logger.info(f"Rate limit, ждём {wait} секунд")
                await asyncio.sleep(wait)
            else:
                await asyncio.sleep(2 ** attempt)

    logger.error(f"Не удалось сгенерировать тест для {subject} после {max_retries} попыток")
    return []