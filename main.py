import os
import asyncio
import random
from flask import Flask, request
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

# Global variables
bot_status = "Not started"
verification_code = None
client_instance = None

@app.route('/')
def home():
    return f"""
    <h1>Telegram Auto Bot</h1>
    <p>Status: {bot_status}</p>
    <p><a href="/start_bot">Start Bot</a></p>
    <p><a href="/enter_code">Enter Verification Code</a></p>
    """

@app.route('/start_bot')
def start_bot():
    global bot_status
    bot_status = "Starting..."
    
    import threading
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    
    return """
    <h1>Bot Started</h1>
    <p>Check your Telegram app for verification code</p>
    <p>Then <a href="/enter_code">enter the code here</a></p>
    """

@app.route('/enter_code')
def enter_code_page():
    return """
    <h1>Enter Verification Code</h1>
    <form action="/submit_code" method="post">
        <input type="text" name="code" placeholder="Enter 5-digit code" required>
        <button type="submit">Verify</button>
    </form>
    """

@app.route('/submit_code', methods=['POST'])
def submit_code():
    global verification_code
    code = request.form.get('code')
    verification_code = code
    logger.info(f"📱 Verification code received: {code}")
    
    return f"""
    <h1>Code Submitted: {code}</h1>
    <p>Bot will now attempt to verify with this code...</p>
    <p><a href="/">Return to Home</a></p>
    """

async def start_telegram_client():
    global client_instance
    
    client_instance = Client(
        "my_account",
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=PHONE_NUMBER
    )
    
    try:
        # Start the client - it will handle verification automatically
        await client_instance.start()
        return True
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False

async def setup_auto_react(client):
    @client.on_message(filters.chat(CHANNEL_USERNAME))
    async def auto_react(client, message: Message):
        try:
            if message.from_user and message.from_user.is_self:
                return
                
            await asyncio.sleep(random.randint(5, 15))
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
            success = await start_telegram_client()
            
            if success and client_instance:
                bot_status = "Connected to Telegram!"
                logger.info("✅ Telegram client started successfully!")
                
                await client_instance.join_chat(CHANNEL_USERNAME)
                logger.info(f"✅ Joined channel: {CHANNEL_USERNAME}")
                
                await setup_auto_react(client_instance)
                logger.info("🤖 Bot is now monitoring channel for new messages...")
                bot_status = "Monitoring channel"
                
                await client_instance.idle()
                
            else:
                bot_status = "Waiting for verification"
                logger.info("📱 Check Telegram app for verification code")
                logger.info("🔄 Retrying in 30 seconds...")
                await asyncio.sleep(30)
                
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            bot_status = f"Error: {e}"
            await asyncio.sleep(30)

def run_bot():
    asyncio.run(main_bot_loop())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
