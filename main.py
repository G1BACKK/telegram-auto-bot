import os
import asyncio
import random
import threading
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

class TelegramBot:
    def __init__(self):
        self.client = None
        self.is_running = False
        
    async def start_bot(self):
        try:
            self.client = TelegramClient('session_name', API_ID, API_HASH)
            
            await self.client.start(phone=PHONE_NUMBER)
            
            if not await self.client.is_user_authorized():
                logger.info("Check your Telegram app for verification code")
                return "Check Telegram for verification code"
            
            me = await self.client.get_me()
            logger.info(f"✅ Logged in as: {me.first_name}")
            
            # Join channel
            channel = await self.client.get_entity(CHANNEL_USERNAME)
            await self.client.join_channel(channel)
            logger.info(f"✅ Joined channel: {CHANNEL_USERNAME}")
            
            # Setup auto-reactor
            @self.client.on(events.NewMessage(chats=channel))
            async def handler(event):
                if not event.message.out:  # Don't react to own messages
                    await asyncio.sleep(random.randint(5, 15))
                    reactions = ['👍', '❤️', '🔥', '⭐', '🎉']
                    await event.message.reply(random.choice(reactions))
                    logger.info(f"✅ Reacted to message in {event.chat.title}")
            
            self.is_running = True
            logger.info("🤖 Bot is now monitoring channel for new messages...")
            
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            self.is_running = False

def run_bot():
    bot = TelegramBot()
    asyncio.run(bot.start_bot())

@app.route('/')
def home():
    return {
        "status": "running",
        "service": "Telegram Auto Bot",
        "message": "Bot is monitoring channel for new posts"
    }

@app.route('/health')
def health():
    return "OK"

@app.route('/start')
def start_bot_route():
    # Start bot in background thread
    if not hasattr(app, 'bot_thread') or not app.bot_thread.is_alive():
        app.bot_thread = threading.Thread(target=run_bot, daemon=True)
        app.bot_thread.start()
        return "Bot starting..."
    return "Bot is already running"

if __name__ == '__main__':
    # Start bot when app starts
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
