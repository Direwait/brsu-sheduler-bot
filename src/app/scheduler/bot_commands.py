# src/app/scheduler/bot_commands.py
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from src.app.scheduler.api_logic import save_user_data, get_groups_by_fakultet_and_course, get_user_data, get_schedule, \
    format_schedule_message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("ФИЗМАТ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выбери факультет", reply_markup=reply_markup)



async def handle_fakultet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fakultet = update.message.text
    user_id = update.effective_user.id

    # Сохраняем факультет
    save_user_data(user_id, 'fakultet', fakultet)

    # Показываем меню курсов
    keyboard = [
        [KeyboardButton("1 КУРС"), KeyboardButton("2 КУРС")],
        [KeyboardButton("3 КУРС"), KeyboardButton("4 КУРС")],
        [KeyboardButton("МАГИСТРАТУРА"), KeyboardButton("НАЗАД")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Факультет: {fakultet}\nВыбери курс:", reply_markup=reply_markup)


async def handle_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    course = update.message.text
    user_id = update.effective_user.id
    save_user_data(user_id, 'course', course)

    # 🎯 ПОЛУЧАЕМ ФАКУЛЬТЕТ ИЗ СЕССИИ
    user_data = get_user_data(user_id)
    fakultet = user_data.get('fakultet')  # Получаем сохраненный факультет

    # 🎯 ПЕРЕДАЕМ ФАКУЛЬТЕТ И КУРС
    groups = get_groups_by_fakultet_and_course(fakultet, course)

    keyboard = []
    row = []
    for group in groups:
        row.append(KeyboardButton(group))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([KeyboardButton("НАЗАД")])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Факультет: {fakultet}\nКурс: {course}\nВыбери группу:", reply_markup=reply_markup)

async def handle_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = update.message.text
    user_id = update.effective_user.id

    user_data = get_user_data(user_id)
    if user_data:
        save_user_data(user_id, 'group', group)
        schedule = get_schedule(user_id, group, user_data['course'])
        save_user_data(user_id, 'schedule', schedule)

        if schedule:
            message = format_schedule_message(schedule, 'all')
            await update.message.reply_text(message)

        # И потом показываем меню дней
        await show_menu(update, schedule)
    else:
        await update.message.reply_text("❌ Ошибка данных")

async def show_menu(update: Update, schedule):
    keyboard = [
        [KeyboardButton("ПН"), KeyboardButton("ВТ"), KeyboardButton("СР")],
        [KeyboardButton("ЧТ"), KeyboardButton("ПТ"), KeyboardButton("СБ")],
        [KeyboardButton("ВСЯ НЕДЕЛЯ"), KeyboardButton("НАЗАД")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    status = "✅ Расписание загружено" if schedule else "❌ Расписание не найдено"
    await update.message.reply_text(f"{status}\nВыбери день:", reply_markup=reply_markup)

async def handle_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = update.message.text
    user_id = update.effective_user.id

    schedule = get_user_data(user_id, 'schedule')
    if schedule:
        day_map = {
            'ПН': ['понед'],
            'ВТ': ['вторник'],
            'СР': ['среда'],
            'ЧТ': ['четверг'],
            'ПТ': ['пятница'],
            'СБ': ['суббота'],
            'ВСЯ НЕДЕЛЯ': 'all'
        }

        # 🎯 УБИРАЕМ 'all' КАК ЗНАЧЕНИЕ ПО УМОЛЧАНИЮ
        days = day_map.get(day)
        if not days:
            await update.message.reply_text("❌ Неизвестный день")
            return

        message = format_schedule_message(schedule, days)
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("❌ Сначала выбери группу")

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text(["ФИЗМАТ"]), handle_fakultet))
    application.add_handler(MessageHandler(filters.Text(["1 КУРС", "2 КУРС", "3 КУРС", "4 КУРС", "МАГИСТРАТУРА"]), handle_course))
    application.add_handler(MessageHandler(filters.Regex(r'^[А-Я]+-\d+$'), handle_group))
    application.add_handler(MessageHandler(filters.Text(["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВСЯ НЕДЕЛЯ"]), handle_day))
    application.add_handler(MessageHandler(filters.Text(["НАЗАД"]), handle_back))