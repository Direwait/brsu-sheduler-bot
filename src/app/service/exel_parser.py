
import xlrd
import requests
from io import BytesIO
from src.app.service.find_url.FileFinder import newest_files



"""Создает матрицу данных с заполненными объединенными ячейками для xlrd"""
def create_matrix_with_merged_cells_xlrd(sheet):
    # Сначала создаем пустую матрицу
    data = []
    for row_idx in range(sheet.nrows):
        row = []
        for col_idx in range(sheet.ncols):
            row.append(sheet.cell_value(row_idx, col_idx))
        data.append(row)

    # Заполняем объединенные ячейки
    for merged_range in sheet.merged_cells:
        rlo, rhi, clo, chi = merged_range
        top_left_value = sheet.cell_value(rlo, clo)

        # Заполняем все ячейки диапазона значением из верхней левой
        for row_idx in range(rlo, rhi):
            for col_idx in range(clo, chi):
                if row_idx < len(data) and col_idx < len(data[row_idx]):
                    data[row_idx][col_idx] = top_left_value
    print(data)
    return data

"""Парсим расписание для указанной группы"""
# Пример использования
def parse_group_schedule(data_matrix, group_name):

    # Находим колонку группы в строке с группами (строка 3)
    groups_row = data_matrix[3]
    group_col = None

    for col_idx, cell in enumerate(groups_row):
        if str(cell).strip() == group_name:
            group_col = col_idx
            break

    if group_col is None:
        print(f"❌ Группа {group_name} не найдена")
        return {}

    print(f"✅ Найдена группа {group_name} в колонке {group_col}")

    # Находим дни недели (ищем строки с названиями дней)
    days = {}
    day_patterns = ['ПОНЕД', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА']

    for row_idx, row in enumerate(data_matrix):
        if row and isinstance(row[0], str):
            cell_text = row[0].upper()
            for day in day_patterns:
                if day in cell_text:
                    days[day] = row_idx
                    print(f"📅 Найден {day} в строке {row_idx}")

    # Парсим расписание для группы
    schedule = {}

    for day_name, day_row_idx in days.items():
        day_lessons = []

        # Всегда получаем 4 пары для каждого дня
        for offset in range(1, 5):  # 1-4 пары
            row_idx = day_row_idx + offset
            time_slot = ""
            lesson_text = "-"  # По умолчанию прочерк

            if row_idx < len(data_matrix):
                row = data_matrix[row_idx]

                # Получаем время пары
                if row and row[0]:
                    time_slot = str(row[0]).strip()

                # Получаем предмет из колонки группы
                if row and group_col < len(row) and row[group_col]:
                    lesson_data = row[group_col]
                    if str(lesson_data).strip():
                        lesson_text = str(lesson_data).strip()

            day_lessons.append({
                'time': time_slot,
                'lesson': lesson_text
            })

            print(f"   🕒 {day_name}, Пара {offset}: {time_slot} - {lesson_text}")

        schedule[day_name] = day_lessons

    return schedule


# итоговый метод
def parse_schedule_with_xlrd(url, group_name, sheet_type=None)->dict:
    try:
        print(f"🔗 Скачиваю файл из: {url}")
        response = requests.get(url)
        response.raise_for_status()

        excel_data = BytesIO(response.content)
        workbook = xlrd.open_workbook(file_contents=excel_data.getvalue(), formatting_info=True)

        print(f"✅ Файл загружен. Листы: {workbook.sheet_names()}")

        all_schedules = {}

        for sheet_idx in range(workbook.nsheets):
            sheet = workbook.sheet_by_index(sheet_idx)
            sheet_name = sheet.name

            print(f"\n🎯 Обрабатываю лист: '{sheet_name}'")

            # 🎯 ПРОСТОЙ ФИЛЬТР ПО ТИПУ ЛИСТА
            if sheet_type:
                sheet_lower = sheet_name.lower()
                type_lower = sheet_type.lower()

                if type_lower == "магистратура":
                    if not any(word in sheet_lower for word in ['м', 'магистр', 'магистратура']):
                        print(f"⏭️  Пропускаем (ищем магистратуру)")
                        continue
                elif type_lower in ["1 курс", "2 курс", "3 курс", "4 курс"]:
                    if type_lower not in sheet_lower:
                        print(f"⏭️  Пропускаем (ищем {sheet_type})")
                        continue

            data_matrix = create_matrix_with_merged_cells_xlrd(sheet)
            group_schedule = parse_group_schedule(data_matrix, group_name)

            if group_schedule:
                all_schedules[sheet_name] = group_schedule
                print(f"✅ Найдено расписание для {group_name}")

        return all_schedules

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {}

def print_schedule(schedule_data, days='all'):
    """
    Универсальная печать расписания

    Args:
        schedule_data: данные расписания
        days: список дней или 'all' для всех
    """
    if not schedule_data:
        print("❌ Нет данных расписания")
        return

    if days == 'all':
        days = list(schedule_data.keys())

    for day in days:
        day_upper = day.upper()
        for schedule_day, lessons in schedule_data.items():
            if day_upper in schedule_day:
                print(f"\n📅 {schedule_day}:")
                for i, lesson in enumerate(lessons, 1):
                    status = "✅" if lesson['lesson'] != "-" else "❌"
                    print(f"   {status} {lesson['time']} - {lesson['lesson']}")
                break

# Использование:
def main():
    url = "https://www.brsu.by/fiziko-matematicheskij-fakultet"
    act, sec = newest_files(url)

    schedule = parse_schedule_with_xlrd(act, "МИ-21", "2 курс")

    if schedule:
        for course_name, days_schedule in schedule.items():
            print(f"\n{'='*50}")
            print(f"📘 {course_name}:")
            print(f"{'='*50}")

            # Вся неделя
            print_schedule(days_schedule, 'all')

            print_schedule(days_schedule, ['понед'])

    else:
        print(f"❌ Расписание не найдено")

if __name__ == "__main__":
    main()
