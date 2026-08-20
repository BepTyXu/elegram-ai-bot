import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Dispatcher, MessageHandler, Filters, CallbackContext
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=4)

def handle_message(update: Update, context: CallbackContext):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
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
        answer = data["choices"][0]["message"]["content"]
    except Exception as e:
        answer = "Извините, произошла ошибка. Попробуйте позже."
        logging.error(e)
    
    update.message.reply_text(answer)

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

@app.route("/webhook", methods=["POST"])
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, bot)
    dispatcher.process_update(update)
    return jsonify({"ok": True})

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
