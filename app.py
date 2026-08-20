import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload, timeout=10)

def get_ai_response(user_text):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://telegram-ai-bot.onrender.com",
                "X-Title": "Telegram AI Bot"
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [{"role": "user", "content": user_text}]
            },
            timeout=30
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("AI ERROR:", str(e))
        return "Извините, произошла ошибка. Попробуйте позже."

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    print("FULL DATA:", str(data)[:1000])
    
    # Обычное сообщение боту
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    
    # Если нет — пробуем business_message (Telegram Business)
    if not chat_id:
        message = data.get("business_message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
    
    # Если нет — пробуем edited_business_message
    if not chat_id:
        message = data.get("edited_business_message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
    
    print("CHAT_ID:", chat_id)
    print("TEXT:", text)
    
    if chat_id and text:
        answer = get_ai_response(text)
        send_message(chat_id, answer)
    else:
        print("NO CHAT_ID OR TEXT — skipping")
    
    return {"ok": True}

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
