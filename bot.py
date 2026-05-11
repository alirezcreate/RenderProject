import telebot

TOKEN = "8369995048:AAG30JkhKOAfx47DJJvWcWiMs1oaAZHfLaU"
ADMIN_ID = 588350538  # آیدی عددی خودت

bot = telebot.TeleBot(TOKEN)

waiting_for_payment = {}

@bot.message_handler(commands=['start'])
def start(message):
    text = """سلام 👋
اطلاعات زیر رو برامون بفرستید:

اسم:
حجم مورد نیاز:

ممنون که مارو انتخاب کردین ❤️"""
    bot.send_message(message.chat.id, text)

# وقتی کاربر اطلاعات ارسال می‌کند
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
    
    waiting_for_payment[message.chat.id] = True

# وقتی ادمین ریپلای می‌کند
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID, content_types=['text'])
def reply_to_user(message):
    if message.reply_to_message:
        # استخراج آیدی کاربر از متن پیام
        lines = message.reply_to_message.text.split("\n")
        user_id_line = [line for line in lines if "آیدی عددی" in line]
        
        if user_id_line:
            user_id = int(user_id_line[0].split(":")[1].strip())
            
            bot.send_message(user_id, message.text)
            bot.send_message(user_id, "📸 لطفاً عکس فیش پرداخت را ارسال کنید.")

# دریافت عکس فیش
@bot.message_handler(content_types=['photo'])
def receive_payment_photo(message):
    if message.chat.id in waiting_for_payment:
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "✅ فیش دریافت شد. محصول به زودی ارسال می‌شود.")
        waiting_for_payment.pop(message.chat.id)

bot.polling()
