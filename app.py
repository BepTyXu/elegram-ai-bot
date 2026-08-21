import os
import time
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

last_reply_time = {}
bot_enabled = True

def send_message(chat_id, text, business_connection_id=None):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if business_connection_id:
        payload["business_connection_id"] = business_connection_id
    resp = requests.post(url, json=payload, timeout=10)
    print("SEND STATUS:", resp.status_code)

def get_ai_response(user_text):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{"text": user_text}]
            }]
        }
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        print("GEMINI STATUS:", response.status_code)
        print("GEMINI BODY:", str(data)[:500])
        
        if "error" in data:
            print("GEMINI API ERROR:", data["error"])
            return "Извините, сервис временно недоступен. Попробуйте позже."
        
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
        if not answer or not answer.strip():
            return "Привет! Чем могу помочь?"
        return answer
    except Exception as e:
        print("GEMINI EXCEPTION:", str(e))
        return "Извините, произошла ошибка. Попробуйте позже."

@app.route("/webhook", methods=["POST"])
def webhook():
    global bot_enabled
    data = request.get_json(force=True)
    
    message = data.get("message") or data.get("business_message") or data.get("edited_business_message") or {}
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    business_connection_id = data.get("business_connection_id") or message.get("business_connection_id")
    
    print("CHAT_ID:", chat_id)
    print("TEXT:", text)
    
    if not chat_id or not text:
        return {"ok": True}
    
    if text.lower().strip() == "/off":
        bot_enabled = False
        send_message(chat_id, "Bot disabled. Type /on to enable.", business_connection_id)
        return {"ok": True}
    
    if text.lower().strip() == "/on":
        bot_enabled = True
        send_message(chat_id, "Bot enabled.", business_connection_id)
        return {"ok": True}
    
    if not bot_enabled:
        return {"ok": True}
    
    now = time.time()
    last = last_reply_time.get(chat_id, 0)
    if now - last < 10:
        print(f"COOLDOWN: skipping chat {chat_id}")
        return {"ok": True}
    
    last_reply_time[chat_id] = now
    answer = get_ai_response(text)
    send_message(chat_id, answer, business_connection_id)
    return {"ok": True}

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
