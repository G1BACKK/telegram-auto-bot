import os
import asyncio
import random
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.tl.functions.phone import JoinGroupCallRequest, CreateGroupCallRequest
from telethon.tl.types import InputPeerChannel
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
    return "🤖 Telegram Auto Bot - Auto Joining Live Streams!"

@app.route('/health')
def health():
    return "OK"

async def join_live_stream_telethon(client, entity):
    """Join live stream using Telethon"""
    try:
        logger.info("🎧 Attempting to join live stream...")
        
        # Method 1: Join existing group call
        try:
            full_chat = await client.get_full_entity(entity)
            if hasattr(full_chat, 'full_chat') and hasattr(full_chat.full_chat, 'call'):
                call = full_chat.full_chat.call
                logger.info(f"📞 Found active call, joining...")
                
                await client(JoinGroupCallRequest(
                    call=call,
                    join_as=await client.get_input_entity(entity),
                    params=await client(GetGroupCallJoinAsRequest(peer=entity))
                ))
                logger.info("✅ SUCCESS: Joined live stream!")
                return True
        except Exception as e:
            logger.info(f"📞 Join existing failed: {e}")
        
        # Method 2: Create new group call
        try:
            logger.info("🔄 Creating new group call...")
            await client(CreateGroupCallRequest(
                peer=entity,
                random_id=random.randint(0, 2147483647)
            ))
            logger.info("✅ SUCCESS: Created and joined group call!")
            return True
        except Exception as e:
            logger.info(f"🔄 Create call failed: {e}")
        
        logger.info("❌ All join methods failed")
        return False
        
    except Exception as e:
        logger.error(f"❌ Live stream join error: {e}")
        return False

async def telegram_bot():
    # Use StringSession for Telethon
    from telethon.sessions import StringSession
    
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    try:
        await client.start()
        me = await client.get_me()
        logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        
        # Get channel entity
        entity = await client.get_entity(CHANNEL_USERNAME)
        logger.info(f"✅ Monitoring: {entity.title}")
        
        try:
            await client.join_chat(CHANNEL_USERNAME)
            logger.info("✅ Joined channel")
        except:
            logger.info("ℹ️ Already in channel")
        
        logger.info("🎯 BOT READY! Auto-joining live streams enabled!")
        
        # MESSAGE HANDLER
        @client.on(events.NewMessage(chats=entity))
        async def handler(event):
            try:
                if event.message.out:
                    return
                
                logger.info(f"📨 New post detected")
                
                # Mark as read (view)
                await event.message.mark_read()
                logger.info("✅ Message viewed")
                
                # React
                await asyncio.sleep(random.randint(3, 8))
                reactions = ['👍', '❤️', '🔥', '⭐', '🎉']
                reaction = random.choice(reactions)
                await event.message.reply(reaction)
                logger.info(f"✅ Reacted: {reaction}")
                
                # Check for live stream
                if event.message.text and any(keyword in event.message.text.lower() for keyword in 
                                            ['live now', 'voice chat', 'stream', 'vc started', '🎧']):
                    logger.info("🎬 LIVE STREAM DETECTED! Joining in 10s...")
                    await asyncio.sleep(10)
                    await join_live_stream_telethon(client, entity)
                
                logger.info("✅ Processing complete")
                
            except Exception as e:
                logger.error(f"❌ Processing error: {e}")
        
        # PERIODIC STREAM CHECK
        async def periodic_check():
            from telethon.tl.functions.phone import GetGroupCallJoinAsRequest
            
            check_count = 0
            while True:
                await asyncio.sleep(180)
                check_count += 1
                logger.info(f"🔍 Periodic check #{check_count}")
                try:
                    await join_live_stream_telethon(client, entity)
                except Exception as e:
                    logger.error(f"❌ Periodic check failed: {e}")
        
        # Start periodic checks
        asyncio.create_task(periodic_check())
        
        # Keep running
        logger.info("🤖 Auto-join monitoring active...")
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def start_bot():
    asyncio.run(telegram_bot())

if __name__ == '__main__':
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
