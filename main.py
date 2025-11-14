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
API_HASH = os.getenv('API_HASH'))
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

app = Flask(__name__)

# Global variable to store verification code
verification_code = None

@app.route('/')
def home():
    return """
    <h1>Telegram Auto Bot</h1>
    <p>Send the verification code to: /set_code/YOUR_CODE</p>
    <p>Example: /set_code/123456</p>
    <p>Then start the bot: /start_bot</p>
    """

@app.route('/set_code/<code>')
def set_code(code):
    global verification_code
    verification_code = code
    return f"Code set: {code}. Now visit /start_bot"

@app.route('/start_bot')
def start_bot_route():
    import threading
    thread = threading.Thread(target=start_bot, daemon=True)
    thread.start()
    return "Bot starting with the code you provided..."

# Auto-react to new messages
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
        # Create client
        client = Client(
            "my_account",
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=PHONE_NUMBER
        )
        
        async with client:
            # Sign in with the code
            if verification_code:
                await client.sign_in(phone_number=PHONE_NUMBER, phone_code=verification_code)
            else:
                await client.start()
            
            logger.info("✅ Telegram client started!")
            
            # Join the channel
            await client.join_chat(CHANNEL_USERNAME)
            logger.info(f"✅ Joined channel: {CHANNEL_USERNAME}")
            
            # Add message handler
            @client.on_message(filters.chat(CHANNEL_USERNAME))
            async def handle_message(client, message):
                await auto_react(client, message)
            
            logger.info("🤖 Bot is now monitoring channel for new messages...")
            
            # Keep running
            await client.idle()
            
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def start_bot():
    asyncio.run(run_telegram_bot())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
