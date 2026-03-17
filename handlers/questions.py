import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from utils.markdown import escape_md
import database

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, edit_message_id=None):
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

    chat_id = update.effective_chat.id
    if edit_message_id:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=edit_message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    else:
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

    await asyncio.sleep(5)

    if user_data["current"] < len(questions):
        await send_question(update, context, edit_message_id=query.message.message_id)
    else:
        await show_result(update, context)

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    score = user_data.get("score", 0)
    total = len(user_data.get("questions", []))

    if user_data.get("mode") == "full_test":
        subject = user_data.get("current_subject")
        if subject:
            if "subject_results" not in user_data:
                user_data["subject_results"] = {}
            user_data["subject_results"][subject] = {"correct": score, "total": total}

        result_text = f"📊 *Предмет {user_data['current_subject_name']} завершён!*\nТвой результат: *{score} из {total}*"
        if total > 0:
            percent = score / total * 100
            result_text += f"  ({percent:.1f}%)"

        await context.bot.edit_message_text(
            chat_id=user_data["current_chat_id"],
            message_id=user_data["current_message_id"],
            text=escape_md(result_text),
            parse_mode=ParseMode.MARKDOWN_V2
        )

        await asyncio.sleep(3)

        subjects_to_do = user_data.get("subjects_to_do", [])
        if subjects_to_do:
            from handlers.full_test import start_next_subject
            await start_next_subject(update, context)
            return
        else:
            from handlers.full_test import finish_full_test
            await finish_full_test(update, context)
            return

    database.update_stats(update.effective_user.id, score, total)
    text = f"📚 *Тест завершён!*\nТвой результат: *{score} из {total}*"
    if total > 0:
        percent = score / total * 100
        text += f"  ({percent:.1f}%)"

    text_escaped = escape_md(text)

    keyboard = [
        [InlineKeyboardButton("🔄 Новый тест", callback_data="new_test")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🏠 В начало", callback_data="back_to_start")]
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
    from handlers.common import start_test_callback
    await start_test_callback(update, context)