import os
import asyncio
import random
import threading
from flask import Flask, request
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

app = Flask(__name__)

# Globals
bot_status = "Not started"
verification_code = None
client_instance = None


# ------------------------------
# FLASK ROUTES
# ------------------------------

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
    
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()

    return """
    <h1>Bot Started</h1>
    <p>Check your Telegram app for verification code.</p>
    <p><a href="/enter_code">Enter the code here</a></p>
    """


@app.route('/enter_code')
def enter_code_page():
    return """
    <h1>Enter Verification Code</h1>
    <form action="/submit_code" method="post">
        <input type="text" name="code" placeholder="Enter Telegram Code" required>
        <button type="submit">Submit</button>
    </form>
    """


@app.route('/submit_code', methods=['POST'])
def submit_code():
    global verification_code
    verification_code = request.form.get('code')
    logger.info(f"📨 Verification code received: {verification_code}")
    
    return f"""
    <h1>Code Submitted</h1>
    <p>Received: {verification_code}</p>
    <p><a href="/">Back to Home</a></p>
    """


# ------------------------------
# TELEGRAM LOGIC
# ------------------------------

async def start_telegram_client():
    global client_instance, verification_code

    async def phone_code_callback():
        """ Wait for user to submit code on Flask page """
        logger.info("⏳ Waiting for verification code from web panel...")
        while verification_code is None:
            await asyncio.sleep(1)

        code = verification_code
        verification_code = None
        logger.info(f"➡ Using code: {code}")
        return code

    client_instance = Client(
        "my_account",  # session file
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=PHONE_NUMBER,
        phone_code=phone_code_callback
    )

    try:
        await client_instance.start()
        return True
    except Exception as e:
        logger.error(f"❌ Authentication error: {e}")
        return False


async def setup_auto_react(client):
    @client.on_message(filters.chat(CHANNEL_USERNAME))
    async def auto_react_handler(client, message: Message):
        try:
            if message.from_user and message.from_user.is_self:
                return

            await asyncio.sleep(random.randint(5, 15))
            emoji_list = ['👍', '❤️', '🔥', '⭐', '🎉']
            reaction = random.choice(emoji_list)

            await message.reply(reaction)
            logger.info(f"💬 Reacted with {reaction} in {message.chat.title}")

        except Exception as e:
            logger.error(f"Error reacting: {e}")


async def main_bot_loop():
    global bot_status, client_instance

    while True:
        try:
            logger.info("🔄 Attempting to start Telegram client...")
            success = await start_telegram_client()

            if success:
                bot_status = "Connected to Telegram"
                logger.info("✅ Telegram client started successfully!")

                # Join channel if not already
                try:
                    await client_instance.join_chat(CHANNEL_USERNAME)
                    logger.info(f"📌 Joined channel: {CHANNEL_USERNAME}")
                except Exception as e:
                    logger.info(f"Already in channel or error: {e}")

                await setup_auto_react(client_instance)
                bot_status = "Monitoring channel"
                logger.info("🤖 Bot is monitoring messages...")

                await client_instance.idle()

            else:
                bot_status = "Waiting for verification code..."
                logger.info("📱 Waiting for code… retrying in 30 seconds")
                await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Fatal bot error: {e}")
            bot_status = f"Error: {e}"
            await asyncio.sleep(30)


def run_bot():
    asyncio.run(main_bot_loop())


# ------------------------------
# START FLASK APP
# ------------------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
