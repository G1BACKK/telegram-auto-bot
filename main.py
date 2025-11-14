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
    return "🤖 Telegram Auto Bot - Monitoring Channel, Reacting & Joining Live Streams!"

@app.route('/health')
def health():
    return "OK"

async def view_recent_posts(client, channel):
    """View recent posts to appear active"""
    try:
        logger.info("👀 Viewing recent posts...")
        async for message in client.get_chat_history(channel.id, limit=5):
            # Simply accessing the message marks it as viewed
            if message.text:
                logger.info(f"👁️ Viewed: {message.text[:50]}...")
            else:
                logger.info("👁️ Viewed media post")
            await asyncio.sleep(2)
        logger.info("✅ Finished viewing recent posts")
    except Exception as e:
        logger.error(f"❌ Error viewing posts: {e}")

async def join_voice_chat(client, chat_id):
    """Join active voice chat/live stream"""
    try:
        # Try to get active group call
        result = await client.invoke(
            raw.functions.phone.GetGroupCall(
                call=await client.invoke(
                    raw.functions.phone.GetGroupCallJoinAs(
                        peer=await client.resolve_peer(chat_id)
                    )
                )
            )
        )
        
        if result.call:
            await client.invoke(
                raw.functions.phone.JoinGroupCall(
                    call=result.call,
                    params=await client.invoke(
                        raw.functions.phone.GetGroupCallJoinAs(
                            peer=await client.resolve_peer(chat_id)
                        )
                    )
                )
            )
            logger.info(f"🎧 SUCCESS: Joined voice chat in channel")
            return True
            
    except Exception as e:
        # Alternative method - try direct join
        try:
            await client.invoke(
                raw.functions.phone.JoinGroupCall(
                    call=raw.types.InputGroupCall(
                        id=0,  # This will try to join any active call
                        access_hash=0
                    ),
                    params=raw.types.DataJSON(data='{}')
                )
            )
            logger.info(f"🎧 SUCCESS: Joined voice chat (alternative method)")
            return True
        except Exception as e2:
            logger.info(f"🎧 No active voice chat or join failed: {e2}")
    
    return False

async def check_and_join_live_streams(client, channel):
    """Check for and join live streams"""
    try:
        logger.info("🔍 Checking for active live streams...")
        
        # Check recent messages for live stream indicators
        async for message in client.get_chat_history(channel.id, limit=15):
            # Check if message indicates live stream
            is_live = False
            
            # Check service messages (voice chat started)
            if message.service:
                service_text = str(message.service)
                if any(keyword in service_text.lower() for keyword in ['voice_chat', 'group_call', 'live']):
                    is_live = True
                    logger.info(f"🎬 Live stream detected via service message")
            
            # Check message text for live keywords
            elif message.text:
                text_lower = message.text.lower()
                live_keywords = [
                    'live now', 'voice chat', 'stream', 'join vc', 
                    'live stream', 'vc started', '🎧', '🔴', 'live:',
                    'streaming', 'watch live', 'tune in'
                ]
                if any(keyword in text_lower for keyword in live_keywords):
                    is_live = True
                    logger.info(f"🎬 Live stream detected via keywords: {message.text[:30]}...")
            
            # If live stream detected, try to join
            if is_live:
                logger.info("🔄 Attempting to join live stream...")
                await asyncio.sleep(5)
                success = await join_voice_chat(client, channel.id)
                if success:
                    return True
                else:
                    logger.info("💤 No active voice chat found to join")
                    break
        
        logger.info("❌ No live streams detected in recent messages")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error checking live streams: {e}")
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
        
        # Get channel properly
        try:
            channel = await client.get_chat(CHANNEL_USERNAME)
            logger.info(f"✅ Found channel: {channel.title}")
        except Exception as e:
            logger.error(f"❌ Cannot access channel {CHANNEL_USERNAME}: {e}")
            return
        
        # Join channel if not already member
        try:
            await client.join_chat(CHANNEL_USERNAME)
            logger.info(f"✅ Joined channel: {channel.title}")
        except Exception as e:
            logger.info(f"ℹ️ Already in channel: {e}")
        
        # Import raw functions for voice chat
        from pyrogram import raw
        
        # Initial activities
        await view_recent_posts(client, channel)  # View recent posts
        await check_and_join_live_streams(client, channel)  # Check for live streams
        
        logger.info("🎯 BOT IS READY! Monitoring for messages, viewing posts & live streams...")
        
        # Auto-react to ALL new messages
        @client.on_message(filters.chat(channel.id))
        async def handle_new_message(client, message: Message):
            try:
                # Don't react to your own messages
                if message.from_user and message.from_user.is_self:
                    return
                
                logger.info(f"📨 New message detected in {message.chat.title}")
                
                # 1. VIEW the message (by accessing it)
                logger.info("👀 Viewing message...")
                
                # 2. REACT to the message
                await asyncio.sleep(random.randint(3, 8))
                try:
                    reaction_emojis = ['👍', '❤️', '🔥', '⭐', '🎉', '👏', '🙏', '😍']
                    reaction = random.choice(reaction_emojis)
                    
                    await client.send_reaction(
                        chat_id=message.chat.id,
                        message_id=message.id,
                        emoji=reaction
                    )
                    logger.info(f"✅ REACTED with {reaction}!")
                    
                except Exception as reaction_error:
                    logger.warning(f"⚠️ Cannot add reaction: {reaction_error}")
                
                # 3. Check if this might be a live stream announcement
                is_live_announcement = False
                if message.service:
                    service_text = str(message.service).lower()
                    if any(keyword in service_text for keyword in ['voice_chat', 'group_call', 'live']):
                        is_live_announcement = True
                elif message.text:
                    text_lower = message.text.lower()
                    live_keywords = ['live now', 'voice chat', 'stream', 'join vc', 'live stream', 'vc started', '🎧']
                    if any(keyword in text_lower for keyword in live_keywords):
                        is_live_announcement = True
                
                # 4. JOIN live stream if announced
                if is_live_announcement:
                    logger.info("🎧 Live stream announcement detected! Joining...")
                    await asyncio.sleep(10)
                    await join_voice_chat(client, channel.id)
                
            except Exception as e:
                logger.error(f"❌ Message handling error: {e}")

        # Periodic activities
        async def periodic_activities():
            activity_count = 0
            while True:
                await asyncio.sleep(300)  # Every 5 minutes
                activity_count += 1
                
                if activity_count % 3 == 0:  # Every 15 minutes
                    logger.info("🔄 Periodic: Viewing recent posts...")
                    await view_recent_posts(client, channel)
                
                if activity_count % 2 == 0:  # Every 10 minutes  
                    logger.info("🔄 Periodic: Checking for live streams...")
                    await check_and_join_live_streams(client, channel)
                
                logger.info(f"📊 Periodic check #{activity_count} completed")
        
        # Start periodic activities
        asyncio.create_task(periodic_activities())
        
        logger.info(f"🤖 Now monitoring: {channel.title}")
        logger.info("✅ Features: Auto-view posts, Auto-react, Auto-join live streams")
        
        # Keep the client running
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
