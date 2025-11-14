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
    return "🤖 Telegram Auto Bot is Running - Monitoring Channel & Live Streams!"

@app.route('/health')
def health():
    return "OK"

async def join_voice_chat(client, chat_id):
    """Join voice chat/live stream"""
    try:
        # Get active voice chats
        voice_chats = await client.get_group_call(chat_id)
        if voice_chats:
            # Join the first active voice chat
            await client.join_group_call(chat_id, voice_chats[0].id)
            logger.info(f"🎧 JOINED voice chat in {chat_id}")
            return True
    except Exception as e:
        logger.info(f"🎧 No active voice chat or already joined: {e}")
    return False

async def check_and_join_live_streams(client, channel):
    """Check for and join live streams"""
    try:
        # Check recent messages for live streams
        async for message in client.get_chat_history(channel.id, limit=10):
            # Look for live stream indicators
            if hasattr(message, 'service') and message.service:
                if 'voice_chat' in str(message.service).lower() or 'live' in str(message.service).lower():
                    logger.info(f"🎬 Live stream detected: {message.service}")
                    await join_voice_chat(client, channel.id)
                    break
                    
            # Also check message text for live stream keywords
            if message.text and any(keyword in message.text.lower() for keyword in ['live', 'voice chat', 'stream', 'vc']):
                logger.info(f"🎬 Possible live stream: {message.text[:50]}...")
                await join_voice_chat(client, channel.id)
                break
                
    except Exception as e:
        logger.error(f"❌ Error checking live streams: {e}")

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
            logger.info(f"📊 Channel ID: {channel.id}")
        except Exception as e:
            logger.error(f"❌ Cannot access channel {CHANNEL_USERNAME}: {e}")
            return
        
        # Join channel if not already member
        try:
            await client.join_chat(CHANNEL_USERNAME)
            logger.info(f"✅ Joined channel: {channel.title}")
        except Exception as e:
            logger.info(f"ℹ️ Already in channel: {e}")
        
        # Check for existing live streams
        await check_and_join_live_streams(client, channel)
        
        logger.info("🎯 BOT IS READY! Monitoring for messages and live streams...")
        
        # Auto-react to messages
        @client.on_message(filters.chat(channel.id))
        async def auto_react(client, message: Message):
            try:
                # Don't react to your own messages
                if message.from_user and message.from_user.is_self:
                    return
                
                logger.info(f"📨 New message: '{message.text[:50] if message.text else 'Media'}...'")
                await asyncio.sleep(random.randint(5, 15))
                
                # Add reaction
                try:
                    reaction_emojis = ['👍', '❤️', '🔥', '⭐', '🎉']
                    reaction = random.choice(reaction_emojis)
                    
                    await client.send_reaction(
                        chat_id=message.chat.id,
                        message_id=message.id,
                        emoji=reaction
                    )
                    logger.info(f"✅ REACTED with {reaction}!")
                    
                except Exception as reaction_error:
                    logger.warning(f"⚠️ Cannot add reaction: {reaction_error}")
                
            except Exception as e:
                logger.error(f"❌ Message handling error: {e}")

        # Monitor for live stream announcements
        @client.on_message(filters.chat(channel.id) & (filters.text | filters.service))
        async def monitor_live_streams(client, message: Message):
            try:
                # Check if this is a live stream announcement
                is_live_announcement = False
                
                # Check service messages (Telegram's live stream notifications)
                if hasattr(message, 'service') and message.service:
                    service_text = str(message.service).lower()
                    if any(keyword in service_text for keyword in ['voice_chat', 'live', 'group_call']):
                        is_live_announcement = True
                        logger.info(f"🎬 SERVICE: Live stream detected via service message")
                
                # Check text for live stream keywords
                elif message.text:
                    text_lower = message.text.lower()
                    live_keywords = ['live now', 'voice chat', 'stream', 'join vc', 'live stream', 'vc started']
                    if any(keyword in text_lower for keyword in live_keywords):
                        is_live_announcement = True
                        logger.info(f"🎬 TEXT: Live stream detected via keywords: {message.text[:50]}...")
                
                # Join if it's a live stream announcement
                if is_live_announcement:
                    logger.info("🎧 Attempting to join voice chat...")
                    await asyncio.sleep(10)  # Wait 10 seconds before joining
                    await join_voice_chat(client, channel.id)
                    
            except Exception as e:
                logger.error(f"❌ Live stream monitoring error: {e}")
        
        logger.info(f"🤖 Monitoring: {channel.title} for messages & live streams")
        
        # Periodic live stream checks
        async def periodic_live_check():
            check_count = 0
            while True:
                await asyncio.sleep(300)  # Check every 5 minutes
                check_count += 1
                logger.info(f"🔍 Periodic live stream check #{check_count}")
                await check_and_join_live_streams(client, channel)
        
        # Start periodic checks
        asyncio.create_task(periodic_live_check())
        
        # Keep the client running
        heartbeat_count = 0
        while True:
            await asyncio.sleep(60)
            heartbeat_count += 1
            if heartbeat_count % 5 == 0:  # Log every 5 minutes
                logger.info(f"💓 Bot running - {heartbeat_count} minutes - Monitoring {channel.title}")
            
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def start_bot():
    asyncio.run(telegram_bot())

if __name__ == '__main__':
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
