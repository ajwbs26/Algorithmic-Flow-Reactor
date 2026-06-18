import telebot

TOKEN = "ISI_TOKEN_BOT"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):

    print()
    print("=" * 50)

    print(
        "CHAT ID :",
        message.chat.id
    )

    print(
        "THREAD ID :",
        message.message_thread_id
    )

    print("=" * 50)
    print()

    bot.reply_to(
        message,
        f"CHAT_ID = {message.chat.id}\n"
        f"THREAD_ID = {message.message_thread_id}"
    )

print("BOT ONLINE")

bot.infinity_polling()