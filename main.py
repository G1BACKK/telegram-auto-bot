import os
import asyncio
import random
import threading
from flask import Flask
from pyrogram import Client, filters, raw
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
    return "🤖 Telegram Auto Bot - Auto Joining Live Streams!"

@app.route('/health')
def health():
    return "OK"

async def increase_view_count(client, message):
    """Working view method"""
    try:
        me = await client.get_me()
        await client.forward_messages(me.id, message.chat.id, message.id)
        logger.info("✅ Message viewed")
        
        await asyncio.sleep(2)
        async for msg in client.get_chat_history(me.id, limit=1):
            await client.delete_messages(me.id, msg.id)
            break
            
        return True
    except Exception as e:
        logger.warning(f"⚠️ View failed: {e}")
        return False

async def join_live_stream_direct(client, channel):
    """Direct method to join live streams"""
    try:
        logger.info("🎧 Attempting to join live stream directly...")
        
        # Method 1: Check for active group calls in the channel
        try:
            # Get full channel info
            channel_full = await client.invoke(
                raw.functions.channels.GetFullChannel(
                    channel=await client.resolve_peer(channel.id)
                )
            )
            
            # Check if there's an active call
            if hasattr(channel_full, 'full_chat') and hasattr(channel_full.full_chat, 'call'):
                call = channel_full.full_chat.call
                logger.info(f"📞 Found active call: {call}")
                
                # Join the call
                await client.invoke(
                    raw.functions.phone.JoinGroupCall(
                        call=call,
                        join_as=await client.resolve_peer((await client.get_me()).id),
                        params=raw.types.DataJSON(data='{"ufrag":"a","pwd":"b","fingerprints":[{"fingerprint":"c","setup":"active","hash":"sha-256"}],"ssrc":123456}')
                    )
                )
                logger.info("✅ SUCCESS: Joined live stream directly!")
                return True
                
        except Exception as e:
            logger.info(f"📞 Direct join failed: {e}")
        
        # Method 2: Create a new group call if none exists
        try:
            logger.info("🔄 Trying to create/join group call...")
            result = await client.invoke(
                raw.functions.phone.CreateGroupCall(
                    peer=await client.resolve_peer(channel.id),
                    random_id=random.randint(0, 2147483647)
                )
            )
            logger.info("✅ SUCCESS: Created and joined group call!")
            return True
            
        except Exception as e:
            logger.info(f"🔄 Create call failed: {e}")
        
        logger.info("❌ All join methods failed")
        return False
        
    except Exception as e:
        logger.error(f"❌ Live stream join error: {e}")
        return False

async def check_and_join_active_streams(client, channel):
    """Periodically check for and join active streams"""
    try:
        logger.info("🔍 Scanning for active live streams...")
        
        # Check recent messages for live stream activity
        active_stream = False
        async for message in client.get_chat_history(channel.id, limit=20):
            # Check if message indicates live stream
            if (message.text and any(keyword in message.text.lower() for keyword in 
                                   ['live now', 'voice chat', 'stream', 'vc started', '🎧', '🔴', 'live stream'])) or \
               (hasattr(message, 'service') and message.service and 'voice_chat' in str(message.service)):
                active_stream = True
                logger.info(f"🎬 Active stream detected in message: {message.text[:50] if message.text else 'Service message'}")
                break
        
        if active_stream:
            logger.info("🔄 Attempting to join detected stream...")
            success = await join_live_stream_direct(client, channel)
            if success:
                return True
            else:
                logger.info("💤 Stream detected but couldn't join automatically")
        else:
            logger.info("❌ No active streams detected")
            
        return False
        
    except Exception as e:
        logger.error(f"❌ Stream check error: {e}")
        return False

async def telegram_bot():
    client = Client(
        "my_account",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING
    )
    
    try:
        await client.start()
        me = await client.get_me()
        logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        
        channel = await client.get_chat(CHANNEL_USERNAME)
        logger.info(f"✅ Monitoring: {channel.title}")
        
        try:
            await client.join_chat(CHANNEL_USERNAME)
            logger.info("✅ Joined channel")
        except:
            logger.info("ℹ️ Already in channel")
        
        # Initial stream check
        await check_and_join_active_streams(client, channel)
        
        logger.info("🎯 BOT READY! Auto-joining live streams enabled!")
        
        # MESSAGE HANDLER
        @client.on_message(filters.chat(channel.id))
        async def handle_message(client, message: Message):
            try:
                if message.from_user and message.from_user.is_self:
                    return
                
                logger.info(f"📨 New post detected")
                
                # 1. VIEW
                await increase_view_count(client, message)
                
                # 2. REACT
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
                
                # 3. CHECK & JOIN LIVE STREAM
                is_live_announcement = False
                if message.text and any(keyword in message.text.lower() for keyword in 
                                      ['live now', 'voice chat', 'stream', 'vc started', '🎧', '🔴 live']):
                    is_live_announcement = True
                    logger.info("🎬 LIVE STREAM ANNOUNCEMENT DETECTED!")
                
                if hasattr(message, 'service') and message.service and 'voice_chat' in str(message.service):
                    is_live_announcement = True
                    logger.info("🎬 VOICE CHAT SERVICE MESSAGE DETECTED!")
                
                if is_live_announcement:
                    logger.info("🔄 Auto-joining live stream in 10 seconds...")
                    await asyncio.sleep(10)
                    await join_live_stream_direct(client, channel)
                
                logger.info("✅ Processing complete")
                
            except Exception as e:
                logger.error(f"❌ Processing error: {e}")
        
        # PERIODIC STREAM CHECKING
        async def periodic_stream_check():
            check_count = 0
            while True:
                await asyncio.sleep(180)  # Check every 3 minutes
                check_count += 1
                logger.info(f"🔍 Periodic stream check #{check_count}")
                await check_and_join_active_streams(client, channel)
        
        # Start periodic checks
        asyncio.create_task(periodic_stream_check())
        
        # Keep running
        logger.info("🤖 Auto-join monitoring active...")
        while True:
            await asyncio.sleep(60)
            
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def start_bot():
    asyncio.run(telegram_bot())

if __name__ == '__main__':
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
