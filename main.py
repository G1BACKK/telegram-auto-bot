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
        await client.start()
        me = await client.get_me()
        logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        
        # Get channel entity properly
        try:
            channel = await client.get_chat(CHANNEL_USERNAME)
            logger.info(f"✅ Found channel: {channel.title}")
        except Exception as e:
            logger.error(f"❌ Cannot access channel {CHANNEL_USERNAME}: {e}")
            return
        
        # Join channel if not already member
        try:
            await client.join_chat(CHANNEL_USERNAME)
            logger.info(f"✅ Joined channel: {channel.title}")
        except Exception as e:
            logger.info(f"ℹ️ Already in channel or can't join: {e}")
        
        logger.info("🎯 BOT IS READY! Post a message in the channel to test!")
        
        # Use the channel ID instead of username for better reliability
        @client.on_message(filters.chat(channel.id))
        async def auto_react(client, message: Message):
            try:
                # Don't react to your own messages
                if message.from_user and message.from_user.is_self:
                    return
                
                logger.info(f"📨 New message detected in {message.chat.title}")
                await asyncio.sleep(random.randint(5, 15))
                
                # Try to add reaction
                try:
                    reaction_emojis = ['👍', '❤️', '🔥', '⭐', '🎉']
                    reaction = random.choice(reaction_emojis)
                    
                    await client.send_reaction(
                        chat_id=message.chat.id,
                        message_id=message.id,
                        emoji=reaction
                    )
                    logger.info(f"✅ REACTED with {reaction}!")
                    
                except Exception as reaction_error:
                    logger.warning(f"⚠️ Cannot react (may need premium): {reaction_error}")
                    # Still log that we viewed the message
                    logger.info(f"👀 Viewed message in {message.chat.title}")
                
            except Exception as e:
                logger.error(f"❌ Message handling error: {e}")
        
        logger.info("🤖 Monitoring channel for new messages...")
        
        # Keep the client running
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            logger.info("💤 Bot is still running and monitoring...")
            
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def start_bot():
    asyncio.run(telegram_bot())

if __name__ == '__main__':
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
