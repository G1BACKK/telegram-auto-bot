import os
import asyncio
import random
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import Message
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

# Global variable to track bot status
bot_status = "Not started"

@app.route('/')
def home():
    return f"""
    <h1>Telegram Auto Bot</h1>
    <p>Status: {bot_status}</p>
    <p><a href="/start_bot">Start Bot</a></p>
    """

@app.route('/start_bot')
def start_bot():
    global bot_status
    bot_status = "Starting..."
    
    # Start bot in background
    import threading
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    
    return """
    <h1>Bot Started</h1>
    <p>Check your Telegram app for verification code</p>
    <p>The bot will automatically retry every 60 seconds</p>
    <p>Check Render logs for status</p>
    """

async def start_telegram_client():
    client = Client(
        "my_account",
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=PHONE_NUMBER
    )
    
    try:
        await client.start()
        return client, True
    except Exception as e:
        logger.error(f"Authentication needed: {e}")
        return None, False

# Auto-react to new messages
async def setup_auto_react(client):
    @client.on_message(filters.chat(CHANNEL_USERNAME))
    async def auto_react(client, message: Message):
        try:
            # Don't react to own messages
            if message.from_user and message.from_user.is_self:
                return
                
            # Wait a bit
            await asyncio.sleep(random.randint(5, 15))
            
            # React with random emoji
            reactions = ['👍', '❤️', '🔥', '⭐', '🎉']
            reaction = random.choice(reactions)
            
            await message.reply(reaction)
            logger.info(f"✅ Reacted with {reaction} to message in {message.chat.title}")
            
        except Exception as e:
            logger.error(f"Error reacting: {e}")

async def main_bot_loop():
    global bot_status
    
    while True:
        try:
            logger.info("🔄 Attempting to start Telegram client...")
            client, success = await start_telegram_client()
            
            if success and client:
                bot_status = "Connected to Telegram!"
                logger.info("✅ Telegram client started successfully!")
                
                # Join the channel
                await client.join_chat(CHANNEL_USERNAME)
                logger.info(f"✅ Joined channel: {CHANNEL_USERNAME}")
                
                # Setup auto-react
                await setup_auto_react(client)
                logger.info("🤖 Bot is now monitoring channel for new messages...")
                bot_status = "Monitoring channel"
                
                # Keep running
                await client.idle()
                
            else:
                bot_status = "Waiting for verification"
                logger.info("📱 Check Telegram app for verification code")
                logger.info("🔄 Retrying in 60 seconds...")
                await asyncio.sleep(60)
                
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            bot_status = f"Error: {e}"
            await asyncio.sleep(60)

def run_bot():
    asyncio.run(main_bot_loop())

if __name__ == '__main__':
    # Start Flask app only
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
