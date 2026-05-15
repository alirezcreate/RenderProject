import telebot
from telebot import types
import sqlite3
import csv
import os
from datetime import datetime

TOKEN = "8369995048:AAG30JkhKOAfx47DJJvWcWiMs1oaAZHfLaU"
ADMIN_ID = 123456789  # آیدی عددی خودت

bot = telebot.TeleBot(TOKEN)

CARD_NUMBER = "6104-3389-0225-0089"

# ------------------ DATABASE ------------------

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    volume INTEGER,
    price INTEGER,
    status TEXT,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    status TEXT
)
""")

conn.commit()

# ------------------ PRICES ------------------

prices = {
    1: 260,
    2: 500,
    3: 730,
    4: 950,
    5: 1150,
    6: 1330,
    7: 1500,
    8: 1660,
    9: 1810,
    10: 1950
}

# ------------------ USER STATES ------------------

user_states = {}

# ------------------ MENUS ------------------

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📦 ثبت سفارش", "🆘 پشتیبانی")
    return markup

def cancel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔙 بازگشت")
    return markup

# ------------------ START ------------------

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    if user_id == ADMIN_ID:
        admin_panel(message)
    else:
        bot.send_message(user_id, "به ربات خوش آمدید 👋", reply_markup=main_menu())

# ------------------ ADMIN PANEL ------------------

def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📦 سفارشات در انتظار", "✅ سفارشات تکمیل شده")
    markup.add("🆘 تیکت‌های باز")
    markup.add("📊 آمار فروش", "👥 تعداد مشتری")
    markup.add("💰 درآمد کل", "📁 خروجی گرفتن")
    bot.send_message(message.chat.id, "پنل مدیریت", reply_markup=markup)

# ------------------ CUSTOMER FLOW ------------------

@bot.message_handler(func=lambda m: m.text == "📦 ثبت سفارش")
def order_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(1, 11):
        markup.add(f"{i} گیگ - {prices[i]} تومان")
    markup.add("🔙 بازگشت")

    user_states[message.chat.id] = "choosing_volume"
    bot.send_message(message.chat.id, "حجم مورد نظر را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and "گیگ" in m.text)
def select_volume(message):
    if user_states.get(message.chat.id) != "choosing_volume":
        return

    volume = int(message.text.split()[0])
    price = prices[volume]

    cursor.execute("""
    INSERT INTO orders (user_id, volume, price, status, date)
    VALUES (?, ?, ?, ?, ?)
    """, (message.chat.id, volume, price, "pending", datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()

    user_states[message.chat.id] = "waiting_payment"

    bot.send_message(
        message.chat.id,
        f"✅ سفارش ثبت شد\n\n💰 مبلغ: {price} تومان\n\n"
        f"شماره کارت جهت پرداخت:\n{CARD_NUMBER}\n\n"
        "پس از پرداخت، فیش را ارسال کنید.",
        reply_markup=cancel_menu()
    )

@bot.message_handler(content_types=['photo'])
def handle_payment(message):
    if user_states.get(message.chat.id) != "waiting_payment":
        return

    cursor.execute("SELECT id FROM orders WHERE user_id=? AND status='pending' ORDER BY id DESC LIMIT 1",
                   (message.chat.id,))
    order = cursor.fetchone()

    if order:
        order_id = order[0]
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.send_message(ADMIN_ID, f"فیش سفارش شماره {order_id}")

        bot.send_message(message.chat.id, "✅ فیش ارسال شد، منتظر تأیید باشید.")
        user_states[message.chat.id] = "none"

# ------------------ SUPPORT ------------------

@bot.message_handler(func=lambda m: m.text == "🆘 پشتیبانی")
def support(message):
    user_states[message.chat.id] = "support"
    bot.send_message(message.chat.id, "پیام خود را ارسال کنید:", reply_markup=cancel_menu())

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == "support")
def support_message(message):
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد.")

# ------------------ ADMIN REPLY SYSTEM ------------------

@bot.message_handler(func=lambda m: m.reply_to_message and m.chat.id == ADMIN_ID)
def admin_reply(message):
    try:
        user_id = message.reply_to_message.forward_from.id
    except:
        return

    if message.content_type == "text":
        bot.send_message(user_id, message.text)
    elif message.content_type == "photo":
        bot.send_photo(user_id, message.photo[-1].file_id)

    cursor.execute("UPDATE orders SET status='completed' WHERE user_id=? AND status='pending'",
                   (user_id,))
    conn.commit()

# ------------------ STATS ------------------

@bot.message_handler(func=lambda m: m.text == "📊 آمار فروش")
def stats(message):
    cursor.execute("SELECT COUNT(*), SUM(price) FROM orders WHERE status='completed'")
    data = cursor.fetchone()
    bot.send_message(message.chat.id,
                     f"✅ تعداد فروش: {data[0] or 0}\n💰 مجموع درآمد: {data[1] or 0} تومان")

@bot.message_handler(func=lambda m: m.text == "👥 تعداد مشتری")
def customers(message):
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    bot.send_message(message.chat.id, f"👥 تعداد کل مشتریان: {count}")

@bot.message_handler(func=lambda m: m.text == "💰 درآمد کل")
def total_income(message):
    cursor.execute("SELECT SUM(price) FROM orders WHERE status='completed'")
    income = cursor.fetchone()[0]
    bot.send_message(message.chat.id, f"💰 درآمد کل: {income or 0} تومان")

# ------------------ EXPORT ------------------

@bot.message_handler(func=lambda m: m.text == "📁 خروجی گرفتن")
def export_data(message):
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()

    with open("orders.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "User ID", "Volume", "Price", "Status", "Date"])
        writer.writerows(rows)

    with open("orders.csv", "rb") as f:
        bot.send_document(message.chat.id, f)

# ------------------

bot.infinity_polling()
    
