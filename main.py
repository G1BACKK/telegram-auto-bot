import os
import asyncio
import random
from telethon import TelegramClient, events
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH') 
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')
SESSION_NAME = 'auto_bot'

class TelegramBot:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        
    async def start_bot(self):
        try:
            await self.client.start(phone=PHONE_NUMBER)
            
            if not await self.client.is_user_authorized():
                await self.client.send_code_request(PHONE_NUMBER)
                code = input("Enter code: ")
                await self.client.sign_in(PHONE_NUMBER, code)
            
            me = await self.client.get_me()
            logger.info(f"Logged in as: {me.first_name}")
            
            # Join channel
            channel = await self.client.get_entity(CHANNEL_USERNAME)
            await self.client.join_channel(channel)
            logger.info(f"Joined channel: {CHANNEL_USERNAME}")
            
            # Setup message handler
            @self.client.on(events.NewMessage(chats=channel))
            async def handler(event):
                if not event.message.out:
                    await asyncio.sleep(random.randint(5, 10))
                    reactions = ['👍', '❤️', '🔥', '⭐']
                    await event.message.reply(random.choice(reactions))
                    logger.info(f"Reacted to message {event.message.id}")
            
            logger.info("Bot is running...")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == '__main__':
    bot = TelegramBot()
    asyncio.run(bot.start_bot())
