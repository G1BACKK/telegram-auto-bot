import os
import asyncio
import random
from flask import Flask
from telethon import TelegramClient, events
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

async def run_bot():
    client = TelegramClient('session_name', API_ID, API_HASH)
    
    await client.start(PHONE_NUMBER)
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE_NUMBER)
        return "Check phone for code"
    
    channel = await client.get_entity(CHANNEL_USERNAME)
    await client.join_channel(channel)
    logger.info("Joined channel")
    
    @client.on(events.NewMessage(chats=channel))
    async def handler(event):
        if not event.message.out:
            await asyncio.sleep(5)
            await event.message.reply('👍')
            logger.info("Reacted to message")
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
