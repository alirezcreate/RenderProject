import telebot

TOKEN = "8369995048:AAG30JkhKOAfx47DJJvWcWiMs1oaAZHfLaU"
ADMIN_ID = 588350538

bot = telebot.TeleBot(TOKEN)

# === سفارشات ===
waiting_for_payment = {}   # user_id -> True (منتظر فیش)
payment_map = {}           # admin_forwarded_message_id -> user_id

# وضعیت سفارش‌ها برای پنل ادمین
orders_pending = {}        # user_id -> order_id (یا True)
orders_completed = set()  # user_id های که کامل شدند

# === پشتیبانی ===
support_waiting = {}       # user_id -> True (مشتری نیازمند پشتیبانی)
support_map = {}           # admin_forwarded_message_id -> user_id

# === منوی ادمین ===
ADMIN_MENU = {
    "support": "مشتری‌های نیاز به پشتیبانی دارن",
    "completed": "سفارشات کامل شده",
    "pending": "سفارش های کامل نشده",
    "back": "بازگشت"
}

# === منوی مشتری ===
CLIENT_MENU = {
    "order": "🛒ثبت سفارش",
    "support": "🧑🏻‍🔧نیاز به پشتیبانی"
}

def get_client_keyboard():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    kb.add(telebot.types.KeyboardButton(CLIENT_MENU["order"]))
    kb.add(telebot.types.KeyboardButton(CLIENT_MENU["support"]))
    return kb

def get_admin_keyboard():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    kb.add(telebot.types.KeyboardButton(ADMIN_MENU["support"]))
    kb.add(telebot.types.KeyboardButton(ADMIN_MENU["pending"]))
    kb.add(telebot.types.KeyboardButton(ADMIN_MENU["completed"]))
    return kb

# -------------------------
# START
# -------------------------
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(
            ADMIN_ID,
            "سلام! پنل ادمین فعال شد.",
            reply_markup=get_admin_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            "سلام 👋 لطفاً یکی از گزینه‌ها رو انتخاب کن:",
            reply_markup=get_client_keyboard()
        )

# -------------------------
# دریافت ثبت سفارش از دکمه
# -------------------------
@bot.message_handler(func=lambda m: m.chat.id != ADMIN_ID and m.text == CLIENT_MENU["order"])
def client_order_clicked(message):
    text = """اطلاعات زیر رو برامون بفرستید:

اسم:
حجم مورد نیاز:

(همینجا پیام رو ارسال کن)"""
    bot.send_message(message.chat.id, text)

# -------------------------
# ارسال متن سفارش به ادمین
# -------------------------
@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID, content_types=['text'])
def handle_text_customer(message):
    # اگر مشتری منوی دکمه پشتیبانی/ثبت سفارش رو زده، اینجا دوباره نگیر
    if message.text in (CLIENT_MENU["order"], CLIENT_MENU["support"]):
        return

    # متن سفارش را به ادمین می‌فرستیم (اگر دکمه ثبت سفارش زده، کاربر احتمالاً همین متن رو می‌فرسته)
    user = message.from_user
    info_text = f"""
📦 سفارش جدید

👤 نام نمایشی: {user.first_name}
🔗 یوزرنیم: @{user.username if user.username else "ندارد"}
🆔 آیدی عددی: {user.id}

📝 متن سفارش:
{message.text}
    """.strip()

    bot.send_message(ADMIN_ID, info_text)
    bot.send_message(
        message.chat.id,
        "✅ اطلاعات شما ارسال شد. پس از تأیید، اطلاعات پرداخت برای شما ارسال می‌شود."
    )

    # برای پنل‌ها وضعیت سفارش رو ثبت می‌کنیم
    orders_pending[user.id] = True

# -------------------------
# دکمه پشتیبانی برای مشتری
# -------------------------
@bot.message_handler(func=lambda m: m.chat.id != ADMIN_ID and m.text == CLIENT_MENU["support"])
def support_clicked(message):
    bot.send_message(
        message.chat.id,
        "لطفاً مشکل‌تون رو در قالب یک پیام و یا همراه با تصویر بفرستین تا ادمین با شما در ارتباط باشه."
    )
    # این کاربر رو منتظر پشتیبانی می‌ذاریم
    support_waiting[message.chat.id] = True

# -------------------------
# دریافت پیام/عکس پشتیبانی از مشتری و ارسال به ادمین
# -------------------------
@bot.message_handler(func=lambda m: m.chat.id != ADMIN_ID, content_types=['text'])
def support_text_handler(message):
    # اگر کاربر در حالت پشتیبانی است، پیام رو به ادمین فوروارد می‌کنیم
    if message.chat.id in support_waiting:
        user = message.from_user
        text = f"""
🆘 پیام پشتیبانی از مشتری

👤 نام نمایشی: {user.first_name}
🔗 یوزرنیم: @{user.username if user.username else "ندارد"}
🆔 آیدی عددی: {user.id}

📝 متن:
{message.text}
        """.strip()

        sent = bot.send_message(ADMIN_ID, text)
        # این message_id مربوط به ادمینه، با ریپلای می‌تونیم کاربر رو پیدا کنیم
        support_map[sent.message_id] = message.chat.id

        bot.send_message(
            message.chat.id,
            "✅ پیام شما به ادمین ارسال شد. لطفاً منتظر پاسخ باشید."
        )

@bot.message_handler(func=lambda m: m.chat.id != ADMIN_ID, content_types=['photo'])
def support_photo_handler(message):
    if message.chat.id in support_waiting:
        user = message.from_user

        sent = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

        # با ریپلای روی همین پیام فوروارد شده، به کاربر می‌رسیم
        support_map[sent.message_id] = message.chat.id

        # مشخصات رو هم کنار فوروارد می‌تونیم بفرستیم (اختیاری)
        # اگر دوست داری، اینجا یک متن مشخصات هم بفرست
        bot.send_message(
            ADMIN_ID,
            f"👤 مشتری: {user.first_name} | @{user.username if user.username else 'ندارد'} | ID: {user.id}"
        )

        bot.send_message(
            message.chat.id,
            "✅ تصویر شما به ادمین ارسال شد. لطفاً منتظر پاسخ باشید."
        )

# -------------------------
# دریافت فیش پرداخت (از مشتری) و فوروارد به ادمین
# -------------------------
@bot.message_handler(content_types=['photo'])
def receive_payment_photo(message):
    # فقط اگر پیام از مشتری باشد (نه ادمین) و منتظر پرداخت باشد
    if message.chat.id == ADMIN_ID:
        return

    if message.chat.id in waiting_for_payment:
        sent = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        payment_map[sent.message_id] = message.chat.id

        bot.send_message(message.chat.id, "✅ فیش دریافت شد. منتظر ارسال فایل محصول باشید.")
        waiting_for_payment.pop(message.chat.id, None)

# نکته: در کد قبلی شما waiting_for_payment را تنظیم نکرده بودیم
# پس برای اینکه جریان کامل شود، بعد از ارسال سفارش به ادمین باید پرداخت فعال شود.
# اما شما گفتی همون کد قبلی خوبه—اینجا برای تکمیل، فرض می‌کنیم ادمین بعد از ریپلای:
# به مشتری پیام می‌ده و ربات مشتری را در waiting_for_payment قرار می‌دهد.
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID, content_types=['text'])
def admin_reply_logic(message):
    # فقط پیام‌هایی که ریپلای هستند
    if not message.reply_to_message:
        return

    # 1) حالت پرداخت: اگر ریپلای روی پیام سفارش کاربر است و متن شامل اطلاعات پرداخت باشد
    # ما قبلاً در کد قبلی روش استخراج user_id از متن را داشتیم، اینجا همان را نگه می‌داریم
    replied = message.reply_to_message
    if not hasattr(replied, "text") or not replied.text:
        return

    # استخراج user_id از خط "آیدی عددی: ..."
    lines = replied.text.split("\n")
    user_id_line = [line for line in lines if "آیدی عددی" in line]

    if user_id_line:
        try:
            user_id = int(user_id_line[0].split(":")[1].strip())
        except:
            return

        # پیام ادمین به معنی ارسال اطلاعات پرداخت به مشتری است
        waiting_for_payment[user_id] = True
        bot.send_message(user_id, message.text)
        return

    # 2) حالت ارسال فایل بعد از فیش: ادمین روی فیش ریپلای می‌کند و فایل می‌فرستد
    # این منطق در handler فایل/عکس در ادامه مدیریت می‌شود.

# -------------------------
# ادمین فایل/عکس را روی فیش ریپلای می‌کند -> ارسال به مشتری
# -------------------------
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID, content_types=['document', 'photo', 'video', 'audio'])
def admin_send_product(message):
    if not message.reply_to_message:
        return

    replied_message_id = message.reply_to_message.message_id

    # آیا این ریپلای مربوط به فیش پرداخت است؟
    if replied_message_id in payment_map:
        user_id = payment_map[replied_message_id]

        if message.content_type == 'document':
            bot.send_document(user_id, message.document.file_id)
        elif message.content_type == 'video':
            bot.send_video(user_id, message.video.file_id)
        elif message.content_type == 'audio':
            bot.send_audio(user_id, message.audio.file_id)
        elif message.content_type == 'photo':
            bot.send_photo(user_id, message.photo[-1].file_id)

        bot.send_message(user_id, "✅ فایل خریداری‌شده برای شما ارسال شد.")
        orders_completed.add(user_id)
        orders_pending.pop(user_id, None)

        return

    # آیا این ریپلای مربوط به پشتیبانی است؟
    if replied_message_id in support_map:
        user_id = support_map[replied_message_id]

        # هر نوع فایل/عکس که ادمین بفرسته، به مشتری ارسال میشه
        if message.content_type == 'document':
            bot.send_document(user_id, message.document.file_id)
        elif message.content_type == 'video':
            bot.send_video(user_id, message.video.file_id)
        elif message.content_type == 'audio':
            bot.send_audio(user_id, message.audio.file_id)
        elif message.content_type == 'photo':
            bot.send_photo(user_id, message.photo[-1].file_id)

        bot.send_message(user_id, "✅ پاسخ/فایل شما برای مشتری ارسال شد.")
        # اگر خواستی بعد از ارسال فایل، پشتیبانی رو ببندیم:
        # support_waiting.pop(user_id, None)
        return

# -------------------------
# منوی پنل ادمین
# -------------------------
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID, content_types=['text'])
def admin_menu(message):
    if message.text == ADMIN_MENU["support"]:
        if not support_waiting:
            bot.send_message(ADMIN_ID, "✅ فعلاً کسی نیاز به پشتیبانی نداره.")
            return

        # ارسال لیست ساده user_id ها
        ids = list(support_waiting.keys())
        bot.send_message(ADMIN_ID, "👥 مشتری‌های نیازمند پشتیبانی:\n" + "\n".join(map(str, ids)))
        return

    if message.text == ADMIN_MENU["pending"]:
        if not orders_pending:
            bot.send_message(ADMIN_ID, "✅ سفارش در حال انتظار نداریم.")
            return
        ids = list(orders_pending.keys())
        bot.send_message(ADMIN_ID, "📌 سفارش‌های کامل‌نشده (user_id):\n" + "\n".join(map(str, ids)))
        return

    if message.text == ADMIN_MENU["completed"]:
        if not orders_completed:
            bot.send_message(ADMIN_ID, "✅ هنوز سفارشی کامل نشده.")
            return
        ids = list(orders_completed)
        bot.send_message(ADMIN_ID, "✅ سفارش‌های کامل‌شده (user_id):\n" + "\n".join(map(str, ids)))
        return

bot.infinity_polling()
        
