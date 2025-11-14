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

# Flask app for health checks
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Auto Bot is Running!"

@app.route('/health')
def health():
    return "OK"

async def telegram_bot():
    # Create client with string session
    client = Client(
        "my_account",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING
    )
    
    try:
        async with client:
            # Get your account info
            me = await client.get_me()
            logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
            
            # Join the target channel with error handling
            try:
                await client.join_chat(CHANNEL_USERNAME)
                logger.info(f"✅ Joined channel: {CHANNEL_USERNAME}")
            except Exception as e:
                logger.error(f"❌ Failed to join channel {CHANNEL_USERNAME}: {e}")
                logger.info("🤖 Bot will still run but won't auto-react")
                return
            
            # Auto-react function
            @client.on_message(filters.chat(CHANNEL_USERNAME))
            async def auto_react(client, message: Message):
                try:
                    # Don't react to your own messages
                    if message.from_user and message.from_user.is_self:
                        return
                    
                    # Random delay (5-15 seconds)
                    delay = random.randint(5, 15)
                    logger.info(f"⏳ Waiting {delay} seconds before reacting...")
                    await asyncio.sleep(delay)
                    
                    # Random reaction
                    reactions = ['👍', '❤️', '🔥', '⭐', '🎉', '👏']
                    reaction = random.choice(reactions)
                    
                    # Send reaction
                    await message.reply(reaction)
                    logger.info(f"✅ Reacted with {reaction} to message in {message.chat.title}")
                    
                except Exception as e:
                    logger.error(f"❌ Error reacting: {e}")
            
            logger.info("🤖 Bot is now monitoring the channel for new messages...")
            logger.info("💤 Waiting for new posts to react...")
            
            # Keep the client running
            await client.idle()
            
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def start_bot():
    asyncio.run(telegram_bot())

if __name__ == '__main__':
    # Start Telegram bot in background thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app (this keeps Render happy)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
