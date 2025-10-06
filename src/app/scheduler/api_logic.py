# src/app/scheduler/app_logic.py
import re

from src.app.service.exel_parser import parse_schedule_with_xlrd
from src.app.service.find_url.FileFinder import newest_files

user_sessions = {}

def save_user_data(user_id, key, value):
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    user_sessions[user_id][key] = value

def get_user_data(user_id, key=None):
    if user_id in user_sessions:
        if key:
            return user_sessions[user_id].get(key)
        return user_sessions[user_id]
    return None


"""Возвращает URL для выбранного факультета"""
def get_fakultet_url(fakultet_name):
    url_map = {
        "ФИЗМАТ": "https://www.brsu.by/fiziko-matematicheskij-fakultet",
        # Добавь другие факультеты когда будут
        # "СПОРТФАК": "https://www.brsu.by/sport-fakultet",
        # "ФИЛФАК": "https://www.brsu.by/filologicheskij-fakultet",
    }
    return url_map.get(fakultet_name)

def get_groups_by_fakultet_and_course(fakultet, course_type):
    fizmat_groups = {
        "1 КУРС": ["МИ-11", "МИ-12", "ФИ-11", "ПМ-11"],
        "2 КУРС": ["МИ-21", "ФИ-21", "ПМ-21"],
        "3 КУРС": ["МИ-31", "ФИ-31", "ПМ-31", "КФ-31"],
        "4 КУРС": ["МИ-41", "ФИ-41", "ПМ-41", "ЭК-41", "КФ-41"],
        "Магистратура": [""]
    }

    sport_groups = {
        "1 КУРС": ["СП-11", "СП-12", "СП-13"],
        "2 КУРС": ["СП-21", "СП-22", "СП-23"],
        # ...
    }

    if fakultet == "ФИЗМАТ":
        return fizmat_groups.get(course_type, [])
    elif fakultet == "СПОРТФАК":
        return sport_groups.get(course_type, [])
    else:
        return []


def format_schedule_messages(schedule_data, days='all'):
    """Форматирует расписание в список сообщений для Telegram, по одному на каждый день."""
    if not schedule_data:
        return ["❌ *Расписание не найдено*"]

    messages = []  # Список для хранения сообщений

    for course_name, days_schedule in schedule_data.items():
        # Для каждого курса
        if days == 'all':
            days_to_show = list(days_schedule.keys())
        else:
            days_to_show = days

        for day in days_to_show:
            message = ""
            day_upper = day.upper()
            for schedule_day, lessons in days_schedule.items():
                if day_upper in schedule_day:
                    txt = schedule_day.upper()
                    message += f"\n📅 *{txt.replace('ПОНЕД', 'ПОНЕДЕЛЬНИК')}*\n"
                    message += "─" * 30 + "\n"
                    has_lessons = False
                    lesson_count = 0

                    for i, lesson in enumerate(lessons, 1):
                        if lesson['lesson'] != "-" and lesson['lesson'].strip():
                            time_display = lesson['time'].replace('пара', '⏰').replace('\n', ' ')
                            time_display = (time_display
                                            .replace('1 ', '1️⃣ ')
                                            .replace('2 ', '2️⃣ ')
                                            .replace('3 ', '3️⃣ ')
                                            .replace('4 ', '4️⃣ ')
                                            )
                            lesson_text = lesson['lesson']

                            message += f"\n{time_display}\n"

                            # 🎯 РАЗБИВАЕМ ПО СТРОКАМ
                            lines = lesson_text.split('\n')

                            for line in lines:
                                line = line.strip()
                                if line:

                                    # 🎯 ЕСЛИ В СТРОКЕ ЕСТЬ ВРЕМЯ И ПОДГРУППА - ВЫВОДИМ КАК ЕСТЬ

                                    time_match = re.search(r'(\d{1,2}\.\d{2})', line)
                                    subgroup_match = re.search(r'(\(\d+\))', line)

                                    if time_match and subgroup_match:
                                        message += f"{line}\n"
                                    elif subgroup_match:
                                        # Только подгруппа - оставляем как есть
                                        message += f"   {line}\n"
                                    else:
                                        # 🎯 ОБЫЧНАЯ ПАРА - КРАСИВО ФОРМАТИРУЕМ
                                        # Ищем аудиторию в конце (цифры)
                                        room_match = re.search(r'(\d+[а-я]?)$', line)
                                        if room_match:
                                            room = room_match.group(1)
                                            # Убираем аудиторию из основного текста
                                            main_text = re.sub(r'\s*\d+[а-я]?$', '', line).strip()
                                            message += f"📚 {main_text}\n"
                                            message += f"🏫 Аудитория: {room}\n"
                                        else:
                                            # Нет аудитории - просто выводим
                                            message += f"📌 {line}\n"

                            has_lessons = True
                            lesson_count += 1

                    if has_lessons:
                        message += f"\n📊 Всего пар: {lesson_count}\n"
                    else:
                        message += "\n🎉 Выходной день!\n"
                    messages.append(message) # Добавляем сформированное сообщение в список

    return messages if messages else ["❌ *Нет пар на выбранные дни*"]


"""Получаем расписание через твои функции"""
#итоговый метод
def get_schedule(user_id, group_name, course_type):

    user_data = get_user_data(user_id)
    if not user_data:
        return {}

    fakultet = user_data.get('fakultet')
    if not fakultet:
        return {}

    # 🎯 ПОЛУЧАЕМ URL ДЛЯ ВЫБРАННОГО ФАКУЛЬТЕТА
    url = get_fakultet_url(fakultet)

    actual,sec = newest_files(url)


    course_map = {
        "1 КУРС": "1 курс",
        "2 КУРС": "2 курс",
        "3 КУРС": "3 курс",
        "4 КУРС": "4 курс",
        "МАГИСТРАТУРА": "магистратура"
    }
    sheet_type = course_map.get(course_type)
    return parse_schedule_with_xlrd(actual, group_name, sheet_type)


def get_all_users():
    """Возвращает копию всех пользовательских сессий"""
    return user_sessions.copy()