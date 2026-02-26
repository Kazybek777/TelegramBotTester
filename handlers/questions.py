import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from utils.markdown import escape_md
import database

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user_data = context.user_data
    idx = user_data["current"]
    questions = user_data["questions"]

    if idx >= len(questions):
        await show_result(update, context)
        return

    q = questions[idx]
    header = f"*Вопрос {idx+1} из {len(questions)}*"
    question_text = q['question']
    full_text = f"{header}\n\n{question_text}"
    text = escape_md(full_text)

    keyboard = []
    for i, opt in enumerate(q["options"]):
        keyboard.append([InlineKeyboardButton(
            escape_md(opt), callback_data=f"ans_{i}"
        )])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    else:
        chat_id = update.effective_chat.id
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )

async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_data = context.user_data
    idx = user_data["current"]
    questions = user_data["questions"]
    q = questions[idx]

    selected = int(query.data.replace("ans_", ""))
    correct = q["correct"]

    if selected == correct:
        user_data["score"] += 1
        feedback = "✅ *Правильно!*"
    else:
        correct_answer = q['options'][correct]
        feedback = f"❌ *Неправильно*. Правильный ответ: {correct_answer}"

    explanation = q["explanation"]
    feedback += f"\n\n{explanation}"

    user_data["current"] += 1

    await query.edit_message_text(
        escape_md(feedback),
        parse_mode=ParseMode.MARKDOWN_V2
    )

    await asyncio.sleep(5)  # время показа объяснений

    if user_data["current"] < len(questions):
        await send_question(update, context)
    else:
        await show_result(update, context)

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    score = user_data.get("score", 0)
    total = len(user_data.get("questions", []))

    database.update_stats(update.effective_user.id, score, total)

    text = f" *Тест завершён!*\nТвой результат: *{score} из {total}*"
    if total > 0:
        percent = score / total * 100
        text += f"  ({percent:.1f}%)"

    text_escaped = escape_md(text)

    keyboard = [
        [InlineKeyboardButton(" Новый тест", callback_data="new_test")],
        [InlineKeyboardButton(" Статистика", callback_data="stats")],
        [InlineKeyboardButton(" В начало", callback_data="back_to_subjects")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text_escaped,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text_escaped,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )

async def new_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    from handlers.common import start_again
    await start_again(query)