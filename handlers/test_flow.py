from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import DIFFICULTIES, QUESTION_COUNTS
from utils.markdown import escape_md
from openrouter_client import generate_test
from handlers.questions import send_question

async def subject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    subject_code = query.data.replace("subj_", "")
    context.user_data["subject"] = subject_code

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"diff_{code}")]
        for code, name in DIFFICULTIES
    ]
    keyboard.append([InlineKeyboardButton(" Назад", callback_data="back_to_subjects")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        escape_md("Выбери уровень сложности:"),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )

async def difficulty_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    difficulty = query.data.replace("diff_", "")
    context.user_data["difficulty"] = difficulty

    keyboard = [
        [InlineKeyboardButton(f"{n} вопросов", callback_data=f"qcount_{n}")]
        for n in QUESTION_COUNTS
    ]
    keyboard.append([InlineKeyboardButton(" Назад", callback_data="back_to_difficulty")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        escape_md("Сколько вопросов будет в тесте?"),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )

async def qcount_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    num = int(query.data.replace("qcount_", ""))
    context.user_data["num_questions"] = num

    await query.edit_message_text(
        escape_md("⏳ Генерирую тест... Подожди немного."),
        parse_mode=ParseMode.MARKDOWN_V2
    )

    subject = context.user_data["subject"]
    difficulty = context.user_data["difficulty"]
    questions = await generate_test(subject, difficulty, num)

    if not questions:
        await query.edit_message_text(
            escape_md(" Не удалось сгенерировать тест. Попробуй позже."),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    context.user_data["questions"] = questions
    context.user_data["current"] = 0
    context.user_data["score"] = 0

    await send_question(update, context)

async def back_to_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"diff_{code}")]
        for code, name in DIFFICULTIES
    ]
    keyboard.append([InlineKeyboardButton(" Назад", callback_data="back_to_subjects")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        escape_md("Выбери уровень сложности:"),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )