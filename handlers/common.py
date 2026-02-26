from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import SUBJECTS
from utils.markdown import escape_md
import database

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    for code, name in SUBJECTS:
        row.append(InlineKeyboardButton(name, callback_data=f"subj_{code}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(" Моя статистика", callback_data="stats")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = " *Привет! Я бот-учитель*\nВыбери предмет для теста или посмотри статистику:"
    await update.message.reply_text(
        escape_md(text),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_stats(update, context)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = database.get_stats(user_id)

    keyboard = []

    if stats and stats["total_tests"] > 0:
        avg = stats["correct_answers"] / stats["total_questions"] * 100
        text = (
            f" *Ваша статистика*\n\n"
            f"• Тестов пройдено: {stats['total_tests']}\n"
            f"• Всего вопросов: {stats['total_questions']}\n"
            f"• Правильных ответов: {stats['correct_answers']}\n"
            f"• Средний балл: {avg:.1f}%"
        )
        # Добавляем кнопку очистки только если есть данные
        keyboard.append([InlineKeyboardButton("🗑 Очистить статистику", callback_data="reset_stats")])
    else:
        text = " Ты ещё не проходил тесты. Начни с /start"

    # Кнопка "Назад" добавляется всегда
    keyboard.append([InlineKeyboardButton(" Назад", callback_data="back_to_subjects")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            escape_md(text),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            escape_md(text),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )

async def reset_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    database.reset_stats(user_id)  # очищаем данные

    await query.edit_message_text(
        escape_md(" Статистика успешно очищена!"),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    # Можно сразу показать обновлённую статистику
    await show_stats(update, context)

async def back_to_subjects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await start_again(query)

async def start_again(query):
    from config import SUBJECTS
    from utils.markdown import escape_md
    keyboard = []
    row = []
    for code, name in SUBJECTS:
        row.append(InlineKeyboardButton(name, callback_data=f"subj_{code}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(" Моя статистика", callback_data="stats")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = " *Привет! Я бот-учитель*\nВыбери предмет для теста или посмотри статистику:"
    await query.edit_message_text(
        escape_md(text),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )