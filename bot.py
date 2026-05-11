import telebot

TOKEN = "8369995048:AAG30JkhKOAfx47DJJvWcWiMs1oaAZHfLaU"
ADMIN_ID = 588350538

bot = telebot.TeleBot(TOKEN)

# user_id -> منتظر فیش
waiting_for_payment = {}

# admin_forwarded_message_id -> user_id
payment_map = {}

@bot.message_handler(commands=['start'])
def start(message):
    text = """سلام 👋
اطلاعات زیر رو برامون بفرستید:

اسم:
حجم مورد نیاز:

ممنون که مارو انتخاب کردین ❤️"""
    bot.send_message(message.chat.id, text)

# دریافت سفارش از کاربر
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID, content_types=['text'])
def forward_to_admin(message):
    user = message.from_user

    info_text = f"""
📦 سفارش جدید

👤 نام نمایشی: {user.first_name}
🔗 یوزرنیم: @{user.username if user.username else "ندارد"}
🆔 آیدی عددی: {user.id}

📝 متن سفارش:
{message.text}
"""

    bot.send_message(ADMIN_ID, info_text)
    bot.send_message(message.chat.id, "✅ اطلاعات شما ارسال شد. پس از تأیید، اطلاعات پرداخت برای شما ارسال می‌شود.")

# دریافت فیش پرداخت
@bot.message_handler(content_types=['photo'])
def receive_payment_photo(message):
    if message.chat.id != ADMIN_ID:
        # فقط اگر کاربر منتظر پرداخت باشد
        if message.chat.id in waiting_for_payment:
            sent = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            payment_map[sent.message_id] = message.chat.id

            bot.send_message(message.chat.id, "😉❤️ فیش دریافت شد✅ پس از تایید٬ فایل براتون ارسال میشه.")
            waiting_for_payment.pop(message.chat.id, None)

# ادمین روی فیش ریپلای می‌کند و فایل محصول می‌فرستد
@bot.message_handler(content_types=['document', 'video', 'audio', 'photo'])
def send_product_to_user(message):
    if message.chat.id != ADMIN_ID:
        return

    if not message.reply_to_message:
        return

    replied_id = message.reply_to_message.message_id

    if replied_id not in payment_map:
        return

    user_id = payment_map[replied_id]

    # اگر ادمین فایل بفرستد، همان فایل به کاربر ارسال می‌شود
    if message.content_type == 'document':
        bot.send_document(user_id, message.document.file_id)
    elif message.content_type == 'video':
        bot.send_video(user_id, message.video.file_id)
    elif message.content_type == 'audio':
        bot.send_audio(user_id, message.audio.file_id)
    elif message.content_type == 'photo':
        bot.send_photo(user_id, message.photo[-1].file_id)

    bot.send_message(user_id, "Enjoy your freedom🚀🌐, support Id @jet1supp")

bot.infinity_polling()
