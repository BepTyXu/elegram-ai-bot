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
                "model": "openrouter/free",
                "messages": [{"role": "user", "content": user_text}]
            },
            timeout=30
        )
        data = response.json()
        print("RAW RESPONSE:", str(data)[:800])
        
        if "error" in data:
            print("API ERROR:", data["error"])
            return "Извините, сервис временно недоступен. Попробуйте позже."
        
        if "choices" not in data or not data["choices"]:
            print("NO CHOICES IN RESPONSE")
            return "Привет! Чем могу помочь?"
        
        answer = data["choices"][0]["message"]["content"]
        
        # Фильтр баговых ответов
        if "User Safety" in answer or not answer.strip():
            return "Привет! Чем могу помочь?"
        
        return answer
    except Exception as e:
        print("EXCEPTION:", str(e))
        return "Извините, произошла ошибка. Попробуйте позже."

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    message = data.get("message") or data.get("business_message") or data.get("edited_business_message") or {}
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    
    if not chat_id:
        chat_id = data.get("chat", {}).get("id")
    
    print("CHAT_ID:", chat_id)
    print("TEXT:", text)
    
    if chat_id and text:
        answer = get_ai_response(text)
        send_message(chat_id, answer)
    
    return {"ok": True}

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
