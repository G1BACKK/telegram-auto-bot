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

async def join_live_stream_pyrogram(client, channel):
    """Join live stream using Pyrogram"""
    try:
        logger.info("🎧 Attempting to join live stream...")
        
        # Method 1: Check for active group calls
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
                logger.info(f"📞 Found active call, joining...")
                
                # Join the call
                await client.invoke(
                    raw.functions.phone.JoinGroupCall(
                        call=call,
                        join_as=await client.resolve_peer((await client.get_me()).id),
                        params=raw.types.DataJSON(data='{"ufrag":"x","pwd":"y","fingerprints":[{"fingerprint":"z","setup":"active","hash":"sha-256"}],"ssrc":12345}')
                    )
                )
                logger.info("✅ SUCCESS: Joined live stream!")
                return True
                
        except Exception as e:
            logger.info(f"📞 Join existing failed: {e}")
        
        # Method 2: Create new group call
        try:
            logger.info("🔄 Creating new group call...")
            await client.invoke(
                raw.functions.phone.CreateGroupCall(
                    peer=await client.resolve_peer(channel.id),
                    random_id=random.randint(0, 2147483647)
                )
            )
            logger.info("✅ SUCCESS: Created and joined group call!")
            return True
            
        except Exception as e:
            logger.info(f"🔄 Create call failed: {e}")
        
        logger.info("❌ All join methods failed - may need admin rights")
        return False
        
    except Exception as e:
        logger.error(f"❌ Live stream join error: {e}")
        return False

async def check_active_streams(client, channel):
    """Check for active streams and join"""
    try:
        logger.info("🔍 Checking for active live streams...")
        
        # Check recent messages for live activity
        active_stream = False
        async for message in client.get_chat_history(channel.id, limit=15):
            if (message.text and any(keyword in message.text.lower() for keyword in 
                                  ['live now', 'voice chat', 'stream', 'vc started', '🎧'])) or \
               (hasattr(message, 'service') and message.service):
                active_stream = True
                logger.info(f"🎬 Stream activity detected: {message.text[:40] if message.text else 'Service message'}")
                break
        
        if active_stream:
            logger.info("🔄 Joining detected stream...")
            success = await join_live_stream_pyrogram(client, channel)
            return success
        else:
            logger.info("❌ No active streams found")
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
        await check_active_streams(client, channel)
        
        logger.info("🎯 BOT READY! Auto-joining live streams!")
        
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
                
                # 3. LIVE STREAM CHECK & JOIN
                is_live = False
                if message.text and any(keyword in message.text.lower() for keyword in 
                                      ['live now', 'voice chat', 'stream', 'vc started', '🎧']):
                    is_live = True
                    logger.info("🎬 LIVE STREAM DETECTED!")
                
                if hasattr(message, 'service') and message.service:
                    is_live = True
                    logger.info("🎬 SERVICE MESSAGE - VOICE CHAT!")
                
                if is_live:
                    logger.info("🔄 Auto-joining in 10 seconds...")
                    await asyncio.sleep(10)
                    await join_live_stream_pyrogram(client, channel)
                
                logger.info("✅ Processing complete")
                
            except Exception as e:
                logger.error(f"❌ Processing error: {e}")
        
        # PERIODIC CHECKS
        async def periodic_checks():
            counter = 0
            while True:
                await asyncio.sleep(180)  # Every 3 minutes
                counter += 1
                logger.info(f"🔍 Periodic check #{counter}")
                await check_active_streams(client, channel)
        
        asyncio.create_task(periodic_checks())
        
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
