import os
import asyncio
import random
import time
from datetime import datetime
from telethon import TelegramClient, events
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Configuration
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
CHANNEL_USERNAMES = [c.strip() for c in os.getenv('CHANNEL_USERNAMES', '').split(',') if c.strip()]
SESSION_NAME = 'auto_telegram_bot'

class TelegramAutoBot:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.joined_channels = []
        
    async def authenticate(self):
        """Handle authentication"""
        try:
            await self.client.start(phone=PHONE_NUMBER)
            
            if not await self.client.is_user_authorized():
                logger.info("First-time setup: Sending verification code...")
                await self.client.send_code_request(PHONE_NUMBER)
                code = input("Enter verification code: ")
                await self.client.sign_in(PHONE_NUMBER, code)
                
            me = await self.client.get_me()
            logger.info(f"Authenticated as: {me.first_name}")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def join_channels(self):
        """Join specified channels"""
        for username in CHANNEL_USERNAMES:
            try:
                if username.startswith('@'):
                    username = username[1:]
                    
                channel = await self.client.get_entity(username)
                await self.client.join_channel(channel)
                self.joined_channels.append(channel)
                logger.info(f"✅ Joined: {username}")
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Failed to join {username}: {e}")
    
    async def react_to_message(self, message):
        """React to a message"""
        try:
            reactions = ['👍', '❤️', '🔥', '⭐']
            reaction = random.choice(reactions)
            
            await asyncio.sleep(random.uniform(5, 15))
            await message.reply(reaction)
            logger.info(f"Reacted with {reaction} to message")
            
        except Exception as e:
            logger.error(f"Failed to react: {e}")
    
    async def monitor_channels(self):
        """Monitor channels for new messages"""
        @self.client.on(events.NewMessage(chats=self.joined_channels))
        async def handler(event):
            message = event.message
            if message.sender_id != (await self.client.get_me()).id:
                logger.info(f"New message in {message.chat.title}")
                await self.react_to_message(message)
    
    async def run(self):
        """Main execution"""
        try:
            if not await self.authenticate():
                return
            
            await self.join_channels()
            
            if not self.joined_channels:
                logger.error("No channels joined")
                return
            
            await self.monitor_channels()
            
            logger.info("🤖 Bot is running...")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Bot crashed: {e}")

# Flask app for health checks
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "running", "time": datetime.now().isoformat()}

@app.route('/health')
def health():
    return "OK"

def start_bot():
    """Start the Telegram bot"""
    bot = TelegramAutoBot()
    asyncio.run(bot.run())

if __name__ == '__main__':
    # For Render, we'll just run Flask
    # The bot will be started manually after verification
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
