import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SUBJECTS = [
    ("math", "Математика"),
    ("physics", "Физика"),
    ("chemistry", "Химия"),
    ("biology", "Биология"),
    ("history", "История"),
    ("geography", "География"),
    ("cs", "Информатика"),
    ("english", "Английский язык"),
]

DIFFICULTIES = [
    ("easy", "Легкий 🟢"),
    ("medium", "Средний 🟡"),
    ("hard", "Сложный 🔴"),
]

# Количество вопросов на один предмет в полном тесте
QUESTIONS_PER_SUBJECT = 5