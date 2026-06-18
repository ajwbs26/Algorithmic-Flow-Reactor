import requests

from telegram.config import (
    BOT_TOKEN,
    CHAT_ID
)

def send_message(text):

    url = (

        f"https://api.telegram.org/bot"
        f"{BOT_TOKEN}"
        f"/sendMessage"
    )

    requests.post(

        url,

        json={

            "chat_id": CHAT_ID,

            "text": text
        },

        timeout=10
    )