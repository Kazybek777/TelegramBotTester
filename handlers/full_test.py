import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import SUBJECTS
from utils.markdown import escape_md
from openrouter_client import client
from handlers.questions import send_question
from handlers.test_flow import safe_send_message
import database

logger = logging.getLogger(__name__)

async def start_next_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    subjects_to_do = user_data.get("subjects_to_do", [])
    all_questions = user_data.get("all_questions", {})

    while subjects_to_do:
        subject_code, subject_name = subjects_to_do[0]
        questions = all_questions.get(subject_code, [])
        if questions:
            subjects_to_do.pop(0)
            user_data["current_subject"] = subject_code
            user_data["current_subject_name"] = subject_name
            user_data["questions"] = questions
            user_data["current"] = 0
            user_data["score"] = 0

            if "current_message_id" in user_data and "current_chat_id" in user_data:
                chat_id = user_data["current_chat_id"]
                message_id = user_data["current_message_id"]
                text = f"📚 *Предмет: {subject_name}*\nЗагружаю первый вопрос..."
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=escape_md(text),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                await send_question(update, context, edit_message_id=message_id)
            else:
                # Первый предмет – создаём новое сообщение
                text = f"📚 *Предмет: {subject_name}*\nЗагружаю первый вопрос..."
                msg = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=escape_md(text),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                user_data["current_message_id"] = msg.message_id
                user_data["current_chat_id"] = msg.chat.id
                await send_question(update, context, edit_message_id=msg.message_id)
            return
        else:
            subjects_to_do.pop(0)

    await finish_full_test(update, context)

async def finish_full_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    results = user_data.get("subject_results", {})
    subject_names = dict(SUBJECTS)

    if not results:
        text = "❌ К сожалению, не удалось сгенерировать ни одного теста. Попробуйте позже или выберите другую сложность."
        keyboard = [
            [InlineKeyboardButton("🔄 Новый тест", callback_data="start_test")],
            [InlineKeyboardButton("🏠 В начало", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await safe_send_message(context, update.effective_chat.id, escape_md(text), ParseMode.MARKDOWN_V2, reply_markup)
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
        return

    lines = ["📊 *Результаты по предметам:*"]
    total_correct = 0
    total_questions = 0
    for code, res in results.items():
        name = subject_names.get(code, code)
        lines.append(f"• {name}: {res['correct']} из {res['total']}")
        total_correct += res['correct']
        total_questions += res['total']
    results_text = "\n".join(lines)

    await safe_send_message(context, update.effective_chat.id,
                            escape_md("🔍 Анализирую твои результаты и подбираю профессию..."),
                            ParseMode.MARKDOWN_V2)

    profession = await get_profession_recommendation_with_retry(results, subject_names)

    database.update_stats(update.effective_user.id, total_correct, total_questions)

    final_text = f"{results_text}\n\n🧑‍🏫 *Рекомендация профессии:*\n{profession}"
    keyboard = [
        [InlineKeyboardButton("🔄 Новый тест", callback_data="start_test")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🏠 В начало", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await safe_send_message(context, update.effective_chat.id,
                                escape_md(final_text),
                                ParseMode.MARKDOWN_V2,
                                reply_markup)
    except Exception as e:
        logger.error(f"Не удалось отправить финальные результаты: {e}")

async def get_profession_recommendation_with_retry(results, subject_names, max_retries=5):
    prompt = "На основе результатов тестирования по школьным предметам пользователя (количество правильных ответов из общего числа вопросов по каждому предмету) порекомендуй одну или несколько профессий, которые могут ему подойти. Объясни свой выбор.\n\n"
    for code, res in results.items():
        name = subject_names.get(code, code)
        prompt += f"{name}: {res['correct']} из {res['total']} правильных ответов.\n"
    prompt += "\nДай рекомендацию в дружественном тоне, на русском языке. Укажи, почему именно эти профессии подходят, учитывая успехи в предметах."

    for attempt in range(max_retries):
        try:
            logger.info(f"Попытка {attempt+1}/{max_retries} получения рекомендации")
            response = await client.chat.completions.create(
                model="openrouter/free",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            content = response.choices[0].message.content
            if content:
                return content
            else:
                logger.warning(f"Пустой ответ от модели (попытка {attempt+1})")
        except Exception as e:
            logger.warning(f"Ошибка при получении рекомендации (попытка {attempt+1}): {e}")
            if hasattr(e, 'status_code') and e.status_code == 429:
                wait = 2 ** attempt * 2
                logger.info(f"Rate limit, ждём {wait} секунд")
                await asyncio.sleep(wait)
            else:
                await asyncio.sleep(2 ** attempt)

    logger.error("Не удалось получить рекомендацию после всех попыток")
    return "Не удалось получить рекомендацию. Попробуйте ещё раз позже."