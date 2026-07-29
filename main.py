import threading
import os
import time
from flask import Flask, render_template_string, request, redirect, url_for
import telebot

TOKEN = "8931754078:AAEhNdrKTNWQ0iZ5kJiK0CRfwuQqvnkmIH8"
ADMIN_CHAT_ID = 5845672092

# ضع رابط موقعك هنا بعد رفعه على الاستضافة المجانية (مثال Render)
WEB_DASHBOARD_URL = "https://your-bot-name.onrender.com"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
app.secret_key = 'sticker_bot_secret_key'

db = {
    "settings": {"maintenance": False},
    "users": {}
}

@bot.message_handler(commands=['start'])
def start_bot(message):
    chat_id = str(message.chat.id)
    name = message.from_user.first_name
    
    if chat_id in db["users"] and db["users"][chat_id].get("banned", False):
        bot.send_message(chat_id, "🚫 عذراً، لقد تم حظرك من استخدام هذا البوت.")
        return

    if db["settings"]["maintenance"] and int(chat_id) != ADMIN_CHAT_ID:
        bot.send_message(chat_id, "⚠️ **البوت في وضع الصيانة حالياً!**\nنعمل على تحديثه، عودوا لاحقاً.", parse_mode="Markdown")
        return

    if chat_id not in db["users"]:
        db["users"][chat_id] = {"name": name, "converted": 0, "banned": False}

    # الأزرار الشفافة
    markup = telebot.types.InlineKeyboardMarkup()
    
    # زر يظهر للأدمن فقط يفتح رابط لوحة التحكم
    if int(chat_id) == ADMIN_CHAT_ID:
        markup.add(telebot.types.InlineKeyboardButton("🌐 لوحة تحكم الويب", url=WEB_DASHBOARD_URL))
    
    markup.add(telebot.types.InlineKeyboardButton("💻 للتواصل مع المطور", url="https://t.me/hinata_xit"))

    welcome_msg = (
        f"✨ أهلاً بك يا *{name}* في بوت التحويل الذكي للملصقات!\n\n"
        "📦 *ما يمكنني فعله لأجلك:*\n"
        "• أرسل لي **ملصقاً متحركاً** 🎬 وسأحوله لك إلى **فيديو متحرك**.\n"
        "• أرسل لي **ملصقاً ثابتاً** 🖼️ وسأحوله لك إلى **صورة عادية**.\n"
        "• يمكنك حفظ النتيجة مباشرة في هاتفك بكل سهولة!\n\n"
        "👇 أرسل ملصقك الآن لنبدأ:"
    )
    
    bot.send_message(chat_id, welcome_msg, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['bc'])
def broadcast_command(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_CHAT_ID:
        return
    
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        bot.reply_to(message, "⚠️ صيغة الأمر خاطئة.\nاستخدمه هكذا:\n`/bc النص الذي تريد إرساله`", parse_mode="Markdown")
        return
    
    bc_text = text_parts[1]
    success_count = 0
    
    for uid in db["users"]:
        try:
            bot.send_message(int(uid), f"📢 **إشعار من الإدارة:**\n\n{bc_text}", parse_mode="Markdown")
            success_count += 1
        except:
            pass
            
    bot.reply_to(message, f"✅ تم إرسال الإذاعة بنجاح إلى ({success_count}) مستخدماً.")

@bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    chat_id = str(message.chat.id)
    
    if chat_id in db["users"] and db["users"][chat_id].get("banned", False):
        bot.send_message(chat_id, "🚫 عذراً، لقد تم حظرك من استخدام هذا البوت.")
        return
    
    if db["settings"]["maintenance"] and int(chat_id) != ADMIN_CHAT_ID:
        bot.send_message(chat_id, "⚠️ البوت في وضع الصيانة حالياً، لا يمكن معالجة طلبك الآن.")
        return

    sticker = message.sticker
    
    try:
        is_animated = sticker.is_animated
        is_video = getattr(sticker, 'is_video', False)
        
        file_info = bot.get_file(sticker.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        if is_animated or is_video:
            bot.send_message(chat_id, "⏳ جاري تحويل الملصق المتحرك إلى فيديو...")
            file_name = "sticker_video.mp4"
            with open(file_name, 'wb') as f:
                f.write(downloaded_file)
                
            with open(file_name, 'rb') as vid:
                bot.send_video(chat_id, vid, caption="✅ تفضل، تم تحويل الملصق المتحرك إلى فيديو متحرك!")
            os.remove(file_name)
        else:
            bot.send_message(chat_id, "⏳ جاري تحويل الملصق الثابت إلى صورة...")
            file_name = "sticker_img.webp"
            with open(file_name, 'wb') as f:
                f.write(downloaded_file)
                
            with open(file_name, 'rb') as img:
                bot.send_photo(chat_id, img, caption="✅ تفضل، تم تحويل الملصق إلى صورة!")
            os.remove(file_name)
            
        if chat_id in db["users"]:
            db["users"][chat_id]["converted"] += 1
            
    except Exception as e:
        bot.send_message(chat_id, "❌ حدث خطأ أثناء المعالجة، حاول مجدداً.")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة تحكم البوت</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
        body { background: #0f172a; color: #f8fafc; padding: 20px; text-align: center; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; max-width: 600px; margin: auto; border: 1px solid #334155; margin-bottom: 20px; text-align: right; }
        .card h2 { text-align: center; color: #38bdf8; margin-bottom: 15px; }
        .btn-maint { background: {{ '#ef4444' if maintenance else '#22c55e' }}; color: white; border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; font-size: 15px; text-decoration: none; display: inline-block; text-align: center; }
        table { width: 100%; margin-top: 15px; border-collapse: collapse; font-size: 13px; }
        th, td { border: 1px solid #334155; padding: 8px; text-align: center; }
        th { background: #334155; color: #38bdf8; }
        .btn-ban { background: #ef4444; padding: 5px 10px; font-size: 12px; border-radius: 5px; color: white; text-decoration: none; display: inline-block; }
        .btn-unban { background: #22c55e; padding: 5px 10px; font-size: 12px; border-radius: 5px; color: white; text-decoration: none; display: inline-block; }
    </style>
</head>
<body>
    <div class="card">
        <h2>⚙️ زر صيانة البوت</h2>
        <p style="margin-bottom: 15px; font-size: 14px; text-align: center;">حالة البوت الحالي: <strong>{{ 'مغلق للصيانة 🛑' if maintenance else 'يعمل بشكل طبيعي ✅' }}</strong></p>
        <form action="/toggle_maintenance" method="POST">
            <button type="submit" class="btn-maint">
                {{ 'إلغاء وضع الصيانة وتشغيل البوت' if maintenance else 'تفعيل وضع الصيانة (إيقاف البوت)' }}
            </button>
        </form>
    </div>

    <div class="card">
        <h2>📊 إدارة المستخدمين وإحصائياتهم</h2>
        <p style="margin-bottom: 10px;">إجمالي المستخدمين: <strong>{{ users|length }}</strong></p>
        <p style="font-size: 13px; color: #94a3b8; margin-bottom: 10px;">💡 للإذاعة السريعة، اكتب في محادثة البوت: <code style="color: #38bdf8;">/bc رسالتك هنا</code></p>
        <table>
            <tr>
                <th>المعرف (ID)</th>
                <th>الاسم</th>
                <th>التحويلات</th>
                <th>الحالة</th>
                <th>تحكم</th>
            </tr>
            {% for uid, u in users.items() %}
            <tr>
                <td>{{ uid }}</td>
                <td>{{ u.name }}</td>
                <td>{{ u.converted }}</td>
                <td>{{ 'محظور 🛑' if u.banned else 'نشط ✅' }}</td>
                <td>
                    {% if u.banned %}
                        <a href="/toggle_ban/{{ uid }}" class="btn-unban">إلغاء الحظر</a>
                    {% else %}
                        <a href="/toggle_ban/{{ uid }}" class="btn-ban">حظر</a>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE, maintenance=db["settings"]["maintenance"], users=db["users"])

@app.route('/toggle_maintenance', methods=['POST'])
def toggle_maintenance():
    db["settings"]["maintenance"] = not db["settings"]["maintenance"]
    return redirect(url_for('dashboard'))

@app.route('/toggle_ban/<uid>')
def toggle_ban(uid):
    if uid in db["users"]:
        db["users"][uid]["banned"] = not db["users"][uid]["banned"]
    return redirect(url_for('dashboard'))

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception as e:
            time.sleep(3)

if __name__ == '__main__':
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
