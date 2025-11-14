import os
import asyncio
import random
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

async def main():
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
            
            # Join the target channel
            await client.join_chat(CHANNEL_USERNAME)
            logger.info(f"✅ Joined channel: {CHANNEL_USERNAME}")
            
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

if __name__ == '__main__':
    # Start the bot
    asyncio.run(main())
