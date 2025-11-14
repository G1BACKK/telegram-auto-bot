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
    return "🤖 Telegram Auto Bot - Viewing & Reacting!"

@app.route('/health')
def health():
    return "OK"

async def increase_view_count(client, message):
    """Actually increase view count by simulating user activity"""
    try:
        # Method 1: Get message details (this often triggers view count)
        try:
            await client.get_messages(message.chat.id, message.id)
            logger.info("✅ Viewed message (method 1)")
        except:
            pass
        
        # Method 2: Use read_chat_history with the specific message
        try:
            await client.read_chat_history(chat_id=message.chat.id, max_id=message.id)
            logger.info("✅ Viewed message (method 2)")
        except:
            pass
        
        # Method 3: Forward message to saved messages (guaranteed view)
        try:
            me = await client.get_me()
            await client.forward_messages(me.id, message.chat.id, message.id)
            logger.info("✅ Viewed message (method 3 - forwarded)")
            # Delete the forwarded message after 2 seconds
            await asyncio.sleep(2)
            async for msg in client.get_chat_history(me.id, limit=1):
                await client.delete_messages(me.id, msg.id)
                break
        except Exception as e:
            logger.warning(f"⚠️ Forward method failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ View failed: {e}")
        return False

async def telegram_bot():
    client = Client(
        "my_account",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING
    )
    
    try:
        # Start client
        await client.start()
        me = await client.get_me()
        logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        
        # Get channel
        channel = await client.get_chat(CHANNEL_USERNAME)
        logger.info(f"✅ Monitoring channel: {channel.title}")
        
        # Join channel
        try:
            await client.join_chat(CHANNEL_USERNAME)
            logger.info("✅ Joined channel")
        except:
            logger.info("ℹ️ Already in channel")
        
        logger.info("🎯 BOT READY! Auto-viewing & reacting active")
        
        # MESSAGE HANDLER - VIEW + REACT
        @client.on_message(filters.chat(channel.id))
        async def handle_message(client, message: Message):
            try:
                # Skip own messages
                if message.from_user and message.from_user.is_self:
                    return
                
                logger.info(f"📨 New message detected")
                
                # 1. IMMEDIATELY VIEW THE MESSAGE (multiple methods)
                await increase_view_count(client, message)
                
                # 2. REACT after short delay
                await asyncio.sleep(random.randint(3, 8))
                try:
                    reactions = ['👍', '❤️', '🔥', '⭐', '🎉']
                    reaction = random.choice(reactions)
                    await client.send_reaction(
                        chat_id=message.chat.id,
                        message_id=message.id,
                        emoji=reaction
                    )
                    logger.info(f"✅ Reacted: {reaction}")
                except Exception as e:
                    logger.warning(f"⚠️ React failed: {e}")
                
                logger.info("✅ Finished processing message")
                
            except Exception as e:
                logger.error(f"❌ Message error: {e}")
        
        # PERIODIC VIEWING OF OLD POSTS
        async def view_old_posts():
            try:
                logger.info("👀 Viewing recent old posts...")
                count = 0
                async for message in client.get_chat_history(channel.id, limit=5):
                    if count < 3:  # View 3 old posts
                        await increase_view_count(client, message)
                        count += 1
                        await asyncio.sleep(2)
                logger.info(f"✅ Viewed {count} old posts")
            except Exception as e:
                logger.error(f"❌ Old posts viewing failed: {e}")
        
        # Start periodic viewing
        asyncio.create_task(view_old_posts())
        
        # Keep bot running
        logger.info("🤖 Bot actively monitoring for new messages...")
        while True:
            await asyncio.sleep(10)
            
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def start_bot():
    asyncio.run(telegram_bot())

if __name__ == '__main__':
    # Start bot in background
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
