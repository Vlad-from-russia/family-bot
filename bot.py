import os
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 🔑 Токен бота (задаётся в Railway → Variables)
TOKEN = os.getenv("TOKEN")

# 📌 ID семейного чата (узнаем через /getchatid)
FAMILY_CHAT_ID = os.getenv("FAMILY_CHAT_ID")

if FAMILY_CHAT_ID:
    FAMILY_CHAT_ID = int(FAMILY_CHAT_ID)

# Хранилище броней (в памяти)
bookings = {
    "ванная": [],
    "туалет": []
}

# /start — только в личке
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    await update.message.reply_text(
        "Привет! Я бот-бронирования 🚪\n"
        "Команды (пиши ТОЛЬКО здесь, в личке):\n"
        "/book <комната> <HH:MM> <минуты>\n"
        "/list — показать все брони\n"
        "/getchatid — узнать ID чата (только в группе)"
    )

# /book — бронь
async def book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    try:
        user = update.effective_user.first_name
        room = context.args[0].lower()
        time_str = context.args[1]
        duration = int(context.args[2])

        if room not in bookings:
            await update.message.reply_text("Такой комнаты нет 😅 (есть: ванная, туалет)")
            return

        # Проверка времени
        start_time = datetime.datetime.strptime(time_str, "%H:%M")
        end_time = start_time + datetime.timedelta(minutes=duration)

        # Проверка пересечений
        for booking in bookings[room]:
            if not (end_time <= booking["start"] or start_time >= booking["end"]):
                await update.message.reply_text("⛔ Это время уже занято!")
                return

        # Добавляем бронь
        bookings[room].append({"user": user, "start": start_time, "end": end_time})

        # Подтверждение в личке
        await update.message.reply_text(
            f"✅ Ты забронировал {room} на {time_str} ({duration} мин.)"
        )

        # Уведомление в семейный чат
        if FAMILY_CHAT_ID:
            text = (
                f"✅ {user} забронировал {room} 🚪\n"
                f"Время: {time_str}\n"
                f"Длительность: {duration} минут"
            )
            await context.bot.send_message(chat_id=FAMILY_CHAT_ID, text=text)

    except Exception:
        await update.message.reply_text("Используй так: /book <комната> <HH:MM> <минуты>")

# /list — список броней
async def list_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    text = "📋 Список броней:\n"
    for room, room_bookings in bookings.items():
        text += f"\n{room.capitalize()}:\n"
        if room_bookings:
            for b in room_bookings:
                text += f"- {b['user']} {b['start'].strftime('%H:%M')}–{b['end'].strftime('%H:%M')}\n"
        else:
            text += "пусто\n"
    await update.message.reply_text(text)

# /getchatid — чтобы узнать ID группы
async def getchatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"ID этого чата: {chat_id}")

# Запуск бота
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("book", book))
    app.add_handler(CommandHandler("list", list_bookings))
    app.add_handler(CommandHandler("getchatid", getchatid))

    print("Бот запущен!")
    app.run_polling()

if _name_ == "_main_":
    main()
