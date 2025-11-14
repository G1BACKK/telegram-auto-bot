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
    return "🤖 Telegram Auto Bot - Viewing, Reacting & Live Streams!"

@app.route('/health')
def health():
    return "OK"

async def increase_view_count(client, message):
    """Increase view count using working methods"""
    try:
        # Method that works: Forward to saved messages
        me = await client.get_me()
        await client.forward_messages(me.id, message.chat.id, message.id)
        logger.info("✅ Message viewed (forwarded to saved)")
        
        # Delete the forwarded message after 2 seconds
        await asyncio.sleep(2)
        async for msg in client.get_chat_history(me.id, limit=1):
            await client.delete_messages(me.id, msg.id)
            break
            
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ View method failed: {e}")
        return False

async def join_live_stream(client, channel):
    """Simple live stream joining attempt"""
    try:
        logger.info("🎧 Checking for live streams...")
        
        # Check recent messages for live stream announcements
        async for message in client.get_chat_history(channel.id, limit=10):
            if message.text and any(keyword in message.text.lower() for keyword in 
                                  ['live now', 'voice chat', 'stream', 'vc started', '🎧', '🔴 live']):
                logger.info(f"🎬 Live stream detected: {message.text[:50]}...")
                
                # Try to join using the live stream link if present
                if 't.me/' in message.text and 'livestream=' in message.text:
                    logger.info("🔗 Live stream link found - attempting to join...")
                    # For now, just log that we detected it
                    # Actual joining requires more complex implementation
                    logger.info("📢 Live stream joining feature ready for implementation")
                    return True
                    
        logger.info("❌ No active live streams found")
        return False
        
    except Exception as e:
        logger.error(f"❌ Live stream check error: {e}")
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
        
        # Check for existing live streams
        await join_live_stream(client, channel)
        
        logger.info("🎯 BOT READY! Auto-viewing & reacting active")
        
        # MESSAGE HANDLER
        @client.on_message(filters.chat(channel.id))
        async def handle_message(client, message: Message):
            try:
                # Skip own messages
                if message.from_user and message.from_user.is_self:
                    return
                
                logger.info(f"📨 New post detected")
                
                # 1. VIEW THE MESSAGE
                await increase_view_count(client, message)
                
                # 2. REACT TO MESSAGE
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
                
                # 3. CHECK FOR LIVE STREAM ANNOUNCEMENT
                if message.text and any(keyword in message.text.lower() for keyword in 
                                      ['live now', 'voice chat', 'stream', 'vc started']):
                    logger.info("🎬 Live stream announcement detected!")
                    await asyncio.sleep(10)
                    await join_live_stream(client, channel)
                
                logger.info("✅ Message processed successfully")
                
            except Exception as e:
                logger.error(f"❌ Message processing error: {e}")
        
        # PERIODIC TASKS
        async def periodic_tasks():
            counter = 0
            while True:
                await asyncio.sleep(300)  # Every 5 minutes
                counter += 1
                
                if counter % 2 == 0:  # Every 10 minutes
                    logger.info("🔄 Periodic live stream check...")
                    await join_live_stream(client, channel)
                
                logger.info(f"📊 Bot active - Cycle {counter}")
        
        # Start periodic tasks
        asyncio.create_task(periodic_tasks())
        
        # Keep bot running
        logger.info("🤖 Bot actively monitoring...")
        while True:
            await asyncio.sleep(60)
            
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
