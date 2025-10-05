# src/app/scheduler/simple_checker.py
import asyncio
from telegram.ext import Application

from src.app.scheduler.api_logic import get_fakultet_url, get_all_users
from src.app.service.find_url.FileFinder import newest_files


async def background_checker(app: Application):
    """Простой фоновый проверяльщик - НЕ ЛОМАЕТ СУЩЕСТВУЮЩИЙ КОД"""
    # Словарь для отслеживания последних версий файлов
    last_files = {}

    print("🔄 Фоновая проверка расписания запущена")

    while True:
        try:
            await asyncio.sleep(1800)  # 30 минут (можно уменьшить для теста)

            print("🔍 Проверяем обновления расписания...")

            # Факультеты из твоего существующего кода
            fakultets = ["ФИЗМАТ"]

            for fakultet in fakultets:
                url = get_fakultet_url(fakultet)
                current_file, previous_file = newest_files(url)

                print(f"📁 {fakultet}: текущий файл - {current_file}")

                # Если это первая проверка - просто сохраняем
                if fakultet not in last_files:
                    last_files[fakultet] = current_file
                    continue

                # Если файл изменился с последней проверки
                if last_files[fakultet] != current_file:
                    print(f"🔄 Обнаружено обновление для {fakultet}!")
                    await notify_fakultet_users(app, fakultet)
                    last_files[fakultet] = current_file  # Обновляем

        except Exception as e:
            print(f"❌ Ошибка в фоновой проверке: {e}")

async def notify_fakultet_users(app: Application, fakultet: str):
    """Уведомляем пользователей конкретного факультета"""
    message = (
        f"📢 *Расписание обновлено!*\n"
        f"Факультет: {fakultet}\n"
        f"Используй /start для получения актуального расписания"
    )

    # Получаем всех пользователей из существующей системы
    all_users = get_all_users()

    notified_count = 0
    for user_id, user_data in all_users.items():
        # Проверяем, что пользователь выбрал этот факультет
        if user_data.get('fakultet') == fakultet:
            try:
                await app.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                notified_count += 1
                print(f"✅ Уведомление отправлено пользователю {user_id}")
            except Exception as e:
                print(f"❌ Не удалось уведомить {user_id}: {e}")

    print(f"📨 Отправлено уведомлений: {notified_count}")