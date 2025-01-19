from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from db_utils import init_db
from users import users
import threading
import time
import asyncio
import warnings
from my_handle import (handle_message, set_profile, start, handle_confirmation, restart_day,
                       log_water, log_food, log_workout, workout_type_selected, check_progress,
                       plot_progress, check_history_progress)

# Suppress the specific DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Function to periodically clean up inactive users
def cleanup_inactive_users():
    while True:
        users.remove_inactive_users()
        # Check for inactive users every hour
        time.sleep(60)

# Основная функция
def main() -> None:
    # init DataBase
    init_db()
    # Start a background thread to clean up inactive users
    cleanup_thread = threading.Thread(target=cleanup_inactive_users, daemon=True)
    cleanup_thread.start()
    # Замените 'TOKEN' на токен вашего бота
    application = Application.builder().token("8077089507:AAHQSG81zdy-JOmdto6m2ve9aeuwZMgw5iU").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("restart_day", restart_day))
    application.add_handler(CallbackQueryHandler(handle_confirmation, pattern='^restart_'))
    application.add_handler(CommandHandler("set_profile", set_profile))
    application.add_handler(CommandHandler("log_water", log_water))
    application.add_handler(CommandHandler("log_food", log_food))
    application.add_handler(CommandHandler("log_workout", log_workout))
    application.add_handler(CallbackQueryHandler(workout_type_selected))

    application.add_handler(CommandHandler("check_progress", check_progress))
    application.add_handler(CommandHandler("check_history_progress", check_history_progress))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

async def update_commands():
    # Create the Application instance with your bot's token
    application = Application.builder().token("8077089507:AAHQSG81zdy-JOmdto6m2ve9aeuwZMgw5iU").read_timeout(30).write_timeout(30).build()
    # Define the commands to be added (only once)
    await application.bot.set_my_commands([
        BotCommand("start", "Запустить бота"),
        BotCommand("restart_day", "Перезапустить день"),
        BotCommand("set_profile", "Настроить профиль"),
        BotCommand("log_water", "Добавить выпитую воду (/log_water <количество>)"),
        BotCommand("log_food", "Добавить потребленную еду (/log_food <название продукта>)"),
        BotCommand("log_workout", "Добавить активность (/log_workout <тип тренировки> <время (мин)>)"),
        BotCommand("check_progress", "Показать прогресс"),
        BotCommand("check_history_progress", "Показать прогресс истории (/check_history_progress <day, week, month или year>)")
    ])

if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(update_commands())
        main()
    except telegram.error.Conflict:
        print("Another instance of the bot is already running.")