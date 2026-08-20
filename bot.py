import os
import logging
from flask import Flask, request
import telebot
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

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
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [{"role": "user", "content": user_text}]
            },
            timeout=30
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(e)
        return "Извините, произошла ошибка. Попробуйте позже."

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, "typing")
    answer = get_ai_response(message.text)
    bot.reply_to(message, answer)

@app.route("/webhook", methods=["POST"])
def webhook():
    json_data = request.get_json(force=True)
    bot.process_new_updates([telebot.types.Update.de_json(json_data)])
    return "ok"

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
