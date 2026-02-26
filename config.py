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
    ("literature", "Литература"),
    ("geography", "География"),
    ("cs", "Информатика"),
    ("english", "Английский язык"),
    ("social", "Обществознание"),
]

DIFFICULTIES = [
    ("easy", "Легкий "),
    ("medium", "Средний "),
    ("hard", "Сложный "),
]

QUESTION_COUNTS = [5, 10, 15, 20]