import asyncio
import os

from dotenv import load_dotenv
from telegram.ext import Application

from src.app.scheduler.back_proces import background_checker
from src.app.scheduler.bot_commands import setup_handlers

load_dotenv()
def main():
    """Запускает бота"""
    # Токен бота из переменных окружения
    BOT_TOKEN = os.getenv('BOT_TOKEN')

    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не найден в .env файле")

    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Настраиваем обработчики
    setup_handlers(application)
    # 🎯 ДОБАВЛЯЕМ ФОНОВУЮ ПРОВЕРКУ (ОДНА СТРОЧКА!)
    # Запускаем бота
    print("🤖 Бот запущен...")
    application.run_polling()
    asyncio.create_task(background_checker(application))

if __name__ == "__main__":
    main()