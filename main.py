import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import TELEGRAM_TOKEN
import database
from handlers.common import (
    start, stats_command, show_stats, reset_stats_callback,
    back_to_start, start_test_callback
)
from handlers.test_flow import fulltest_difficulty_callback
from handlers.questions import answer_callback, new_test_callback

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    database.init_db()

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))

    app.add_handler(CallbackQueryHandler(start_test_callback, pattern="^start_test$"))
    app.add_handler(CallbackQueryHandler(fulltest_difficulty_callback, pattern="^fulltest_diff_"))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    app.add_handler(CallbackQueryHandler(answer_callback, pattern="^ans_"))
    app.add_handler(CallbackQueryHandler(new_test_callback, pattern="^new_test$"))
    app.add_handler(CallbackQueryHandler(show_stats, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(reset_stats_callback, pattern="^reset_stats$"))

    logger.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()