import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import TimedOut, RetryAfter
from config import SUBJECTS, QUESTIONS_PER_SUBJECT
from openrouter_client import generate_test
from utils.markdown import escape_md

logger = logging.getLogger(__name__)

async def safe_send_message(context, chat_id, text, parse_mode=None, reply_markup=None, retries=3):
    for attempt in range(retries):
        try:
            return await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        except (TimedOut, RetryAfter) as e:
            logger.warning(f"Ошибка отправки сообщения (попытка {attempt+1}/{retries}): {e}")
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Неизвестная ошибка отправки: {e}")
            raise

async def fulltest_difficulty_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    difficulty = query.data.replace("fulltest_diff_", "")
    context.user_data["difficulty"] = difficulty
    context.user_data["mode"] = "full_test"
    context.user_data["subjects_to_do"] = list(SUBJECTS)
    context.user_data["subject_results"] = {}

    await query.edit_message_text(
        escape_md("⏳ Генерирую тесты по всем предметам... Это может занять до минуты."),
        parse_mode=ParseMode.MARKDOWN_V2
    )

    tasks = []
    for code, name in SUBJECTS:
        tasks.append(generate_test(code, difficulty, QUESTIONS_PER_SUBJECT))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_questions = {}
    failed_subjects = []
    for (code, name), res in zip(SUBJECTS, results):
        if isinstance(res, Exception) or not res:
            failed_subjects.append(name)
            all_questions[code] = []
        else:
            all_questions[code] = res

    context.user_data["all_questions"] = all_questions

    if failed_subjects:
        result_text = f"⚠️ Не удалось сгенерировать тесты для: {', '.join(failed_subjects)}. Они будут пропущены."
    else:
        result_text = "✅ Все тесты успешно сгенерированы! Начинаем..."

    await query.edit_message_text(
        escape_md(result_text),
        parse_mode=ParseMode.MARKDOWN_V2
    )

    from handlers.full_test import start_next_subject
    await start_next_subject(update, context)