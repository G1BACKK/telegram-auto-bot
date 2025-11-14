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
    return "🤖 Telegram Auto Bot - Basic Version Running!"

@app.route('/health')
def health():
    return "OK"

async def simple_telegram_bot():
    """Simple version that just works"""
    client = Client(
        "my_account",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING
    )
    
    try:
        # Start client
        await client.start()
        me = await client.get_me()
        logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        
        # Get channel
        channel = await client.get_chat(CHANNEL_USERNAME)
        logger.info(f"✅ Monitoring channel: {channel.title}")
        
        # Join channel
        try:
            await client.join_chat(CHANNEL_USERNAME)
            logger.info("✅ Joined channel")
        except:
            logger.info("ℹ️ Already in channel")
        
        logger.info("🎯 BOT READY! Basic functions active")
        
        # SIMPLE MESSAGE HANDLER - JUST REACT FOR NOW
        @client.on_message(filters.chat(channel.id))
        async def handle_message(client, message: Message):
            try:
                # Skip own messages
                if message.from_user and message.from_user.is_self:
                    return
                
                logger.info(f"📨 New message: {message.text[:30] if message.text else 'Media'}")
                
                # 1. Mark as read (simple view)
                try:
                    await client.read_chat_history(chat_id=message.chat.id)
                    logger.info("👀 Marked as read")
                except Exception as e:
                    logger.warning(f"⚠️ View failed: {e}")
                
                # 2. React to message
                await asyncio.sleep(random.randint(3, 8))
                try:
                    reactions = ['👍', '❤️', '🔥', '⭐', '🎉']
                    reaction = random.choice(reactions)
                    await client.send_reaction(
                        chat_id=message.chat.id,
                        message_id=message.id,
                        emoji=reaction
                    )
                    logger.info(f"✅ Reacted: {reaction}")
                except Exception as e:
                    logger.warning(f"⚠️ React failed: {e}")
                
            except Exception as e:
                logger.error(f"❌ Message error: {e}")
        
        # Keep bot running
        logger.info("🤖 Bot monitoring for messages...")
        while True:
            await asyncio.sleep(10)
            
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def start_bot():
    asyncio.run(simple_telegram_bot())

if __name__ == '__main__':
    # Start bot in background
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
