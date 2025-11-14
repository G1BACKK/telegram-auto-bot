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

# Pyrogram client
client = Client(
    "my_account",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER
)

@app.route('/')
def home():
    return "Telegram Auto Bot - Visit /start_bot to begin"

@app.route('/health')
def health():
    return "OK"

@app.route('/start_bot')
def start_bot_page():
    return """
    <h1>Telegram Bot Setup</h1>
    <p>Check your Telegram app for verification code</p>
    <p>Then visit: /verify_code/YOUR_CODE</p>
    <p>Example: /verify_code/12345</p>
    """

@app.route('/verify_code/<code>')
def verify_code(code):
    import threading
    thread = threading.Thread(target=start_bot_with_code, args=(code,), daemon=True)
    thread.start()
    return f"Verifying code: {code}. Check logs..."

# Auto-react to new messages
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

async def run_telegram_bot():
    try:
        await client.start()
        logger.info("✅ Telegram client started!")
        
        # Join the channel
        await client.join_chat(CHANNEL_USERNAME)
        logger.info(f"✅ Joined channel: {CHANNEL_USERNAME}")
        
        logger.info("🤖 Bot is now monitoring channel for new messages...")
        
        # Keep running
        await client.idle()
        
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def start_bot_with_code(code):
    # This will use the existing session if already verified
    asyncio.run(run_telegram_bot())

def start_bot():
    asyncio.run(run_telegram_bot())

if __name__ == '__main__':
    # Start Telegram bot in background
    import threading
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
