import os
import asyncio
import random
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import Message
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_STRING = os.getenv('SESSION_STRING')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Auto Bot is Running and Monitoring Channel!"

@app.route('/health')
def health():
    return "OK"

async def telegram_bot():
    client = Client(
        "my_account",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING
    )
    
    try:
        async with client:
            me = await client.get_me()
            logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
            
            # Join channel
            await client.join_chat(CHANNEL_USERNAME)
            logger.info(f"✅ Joined channel: {CHANNEL_USERNAME}")
            
            # Log that bot is ready
            logger.info("🎯 BOT IS READY! Post a message in the channel to test!")
            
            @client.on_message(filters.chat(CHANNEL_USERNAME))
            async def auto_react(client, message: Message):
                if message.from_user and message.from_user.is_self:
                    return
                
                logger.info(f"📨 New message detected: {message.text[:50] if message.text else 'Media message'}")
                await asyncio.sleep(random.randint(5, 15))
                
                reactions = ['👍', '❤️', '🔥', '⭐', '🎉']
                reaction = random.choice(reactions)
                await message.reply(reaction)
                logger.info(f"✅ REACTED with {reaction}!")
            
            logger.info("🤖 Monitoring channel for new messages...")
            await client.idle()
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")

def start_bot():
    asyncio.run(telegram_bot())

if __name__ == '__main__':
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
