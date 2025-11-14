import os
import asyncio
import random
import time
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import InputMessagesFilterPhotos, InputMessagesFilterVideo
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)

# Configuration from environment variables
API_ID = int(os.getenv('API_ID', ''))
API_HASH = os.getenv('API_HASH', '')
PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
CHANNEL_USERNAMES = os.getenv('CHANNEL_USERNAMES', '').split(',')  # Multiple channels
SESSION_NAME = 'auto_telegram_bot'

# Reactions configuration
REACTIONS = ['👍', '❤️', '🔥', '⭐', '🎉', '👏', '🙏', '😍']
REACTION_DELAY = (5, 15)  # Random delay between 5-15 seconds
VIEW_DELAY = (2, 8)       # Delay before viewing messages

class TelegramAutoBot:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.joined_channels = []
        
    async def authenticate(self):
        """Handle authentication with phone verification"""
        try:
            await self.client.start(phone=PHONE_NUMBER)
            
            if not await self.client.is_user_authorized():
                logger.info("First-time setup: Sending verification code...")
                await self.client.send_code_request(PHONE_NUMBER)
                code = input("Enter the verification code sent to your Telegram: ")
                await self.client.sign_in(PHONE_NUMBER, code)
                
            me = await self.client.get_me()
            logger.info(f"Successfully authenticated as: {me.first_name} (@{me.username})")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def join_channels(self):
        """Join all specified channels"""
        for channel_username in CHANNEL_USERNAMES:
            channel_username = channel_username.strip()
            if not channel_username:
                continue
                
            try:
                # Remove @ if present
                if channel_username.startswith('@'):
                    channel_username = channel_username[1:]
                    
                channel = await self.client.get_entity(channel_username)
                await self.client.join_channel(channel)
                self.joined_channels.append(channel)
                logger.info(f"✅ Successfully joined channel: {channel_username}")
                
                # Small delay between joins
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"❌ Failed to join {channel_username}: {e}")
    
    async def react_to_message(self, message, reaction):
        """React to a specific message"""
        try:
            await asyncio.sleep(random.uniform(*REACTION_DELAY))
            await message.reply(reaction)
            logger.info(f"Reacted with {reaction} to message {message.id} in {message.chat.title}")
        except Exception as e:
            logger.error(f"Failed to react to message {message.id}: {e}")
    
    async def view_recent_messages(self, channel, limit=10):
        """View recent messages to appear active"""
        try:
            async for message in self.client.iter_messages(channel, limit=limit):
                # Simply accessing the message marks it as viewed
                logger.info(f"Viewed message {message.id} in {channel.title}")
                await asyncio.sleep(random.uniform(*VIEW_DELAY))
                
        except Exception as e:
            logger.error(f"Error viewing messages in {channel.title}: {e}")
    
    async def handle_new_messages(self):
        """Setup event handler for new messages"""
        @self.client.on(events.NewMessage(chats=self.joined_channels))
        async def new_message_handler(event):
            message = event.message
            if message.sender_id != (await self.client.get_me()).id:  # Don't react to own messages
                logger.info(f"New message detected in {message.chat.title}: {message.text[:50] if message.text else 'Media message'}")
                
                # Choose random reaction
                reaction = random.choice(REACTIONS)
                
                # React to the message
                await self.react_to_message(message, reaction)
    
    async def periodic_activities(self):
        """Perform periodic activities to stay active"""
        while True:
            try:
                for channel in self.joined_channels:
                    # View some recent messages
                    await self.view_recent_messages(channel, limit=5)
                    
                    # Random delay between channel activities
                    await asyncio.sleep(random.uniform(30, 60))
                
                # Wait 1-2 hours before next round of activities
                wait_time = random.uniform(3600, 7200)  # 1-2 hours
                logger.info(f"Next periodic activities in {wait_time/60:.1f} minutes")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Error in periodic activities: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def run(self):
        """Main execution function"""
        try:
            # Authenticate
            if not await self.authenticate():
                return
            
            # Join channels
            await self.join_channels()
            
            if not self.joined_channels:
                logger.error("No channels joined. Exiting.")
                return
            
            # Setup message handler
            await self.handle_new_messages()
            
            logger.info("🤖 Bot is now running and monitoring channels...")
            logger.info(f"Monitoring {len(self.joined_channels)} channels")
            
            # Start periodic activities in background
            asyncio.create_task(self.periodic_activities())
            
            # Keep the client running
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            # Wait before restarting
            await asyncio.sleep(60)

# Health check for Render
from flask import Flask
app = Flask(__name__)

@app.route('/')
def health_check():
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "service": "Telegram Auto Bot"
    }

@app.route('/health')
def health():
    return "OK", 200

async def run_bot():
    bot = TelegramAutoBot()
    await bot.run()

def start_services():
    """Start both Flask app and Telegram bot"""
    import threading
    
    # Start Flask app in a thread
    def run_flask():
        app.run(host='0.0.0.0', port=5000, debug=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start Telegram bot in main thread
    asyncio.run(run_bot())

if __name__ == '__main__':
    start_services()
