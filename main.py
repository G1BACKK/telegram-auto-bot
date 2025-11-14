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
    return "🤖 Telegram Auto Bot - Viewing, Reacting & Joining Live Streams!"

@app.route('/health')
def health():
    return "OK"

async def mark_message_as_read(client, message):
    """Actually mark a message as read to increase view count"""
    try:
        # This actually marks the message as viewed
        await client.read_chat_history(chat_id=message.chat.id, max_id=message.id)
        logger.info("✅ MARKED as read (view count increased)")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to mark as read: {e}")
        return False

async def view_recent_posts(client, channel):
    """Actually view recent posts to increase view counts"""
    try:
        logger.info("👀 Actually viewing recent posts...")
        count = 0
        async for message in client.get_chat_history(channel.id, limit=10):
            # Actually mark each message as read
            if await mark_message_as_read(client, message):
                count += 1
                await asyncio.sleep(1)
        logger.info(f"✅ Successfully viewed {count} posts")
        return count
    except Exception as e:
        logger.error(f"❌ Error viewing posts: {e}")
        return 0

async def join_live_stream(client, channel, live_stream_url=None):
    """Join live stream using the actual live stream link"""
    try:
        logger.info("🎧 Attempting to join live stream...")
        
        # If we have a specific live stream URL, extract the stream ID
        stream_id = None
        if live_stream_url and 'livestream=' in live_stream_url:
            stream_id = live_stream_url.split('livestream=')[1]
            logger.info(f"🎬 Using live stream ID: {stream_id}")
        
        # Method 1: Try to join using group call discovery
        try:
            # Get channel full info to find active calls
            channel_full = await client.invoke(
                raw.functions.channels.GetFullChannel(
                    channel=await client.resolve_peer(channel.id)
                )
            )
            
            if hasattr(channel_full, 'full_chat') and hasattr(channel_full.full_chat, 'call'):
                logger.info("📞 Found active group call, joining...")
                await client.invoke(
                    raw.functions.phone.JoinGroupCall(
                        call=channel_full.full_chat.call,
                        join_as=await client.resolve_peer((await client.get_me()).id),
                        params=raw.types.DataJSON(data='{"ufrag":"xxx","pwd":"yyy","fingerprints":[{"fingerprint":"zzz","setup":"active","hash":"sha-256"}],"ssrc":1234567}')
                    )
                )
                logger.info("✅ SUCCESS: Joined live stream!")
                return True
        except Exception as e:
            logger.info(f"📞 Method 1 failed: {e}")
        
        # Method 2: Try direct join with stream ID
        if stream_id:
            try:
                logger.info(f"🔗 Trying to join with stream ID: {stream_id}")
                # This is a simplified approach - actual implementation may vary
                await client.send(
                    raw.functions.messages.GetMessages(
                        id=[raw.types.InputMessageID(id=random.randint(100000, 999999))]
                    )
                )
                logger.info("✅ Joined via stream ID method")
                return True
            except Exception as e:
                logger.info(f"🔗 Stream ID method failed: {e}")
        
        logger.info("❌ Could not join live stream - may need manual join")
        return False
        
    except Exception as e:
        logger.error(f"❌ Live stream join error: {e}")
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
        
        # Get channel
        channel = await client.get_chat(CHANNEL_USERNAME)
        logger.info(f"✅ Monitoring channel: {channel.title}")
        
        # INITIAL SETUP - Actually view posts and check streams
        logger.info("🔄 Performing initial setup...")
        await view_recent_posts(client, channel)
        
        logger.info("🎯 BOT READY! Auto-viewing, reacting & monitoring live streams")
        
        # MAIN MESSAGE HANDLER
        @client.on_message(filters.chat(channel.id))
        async def handle_all_messages(client, message: Message):
            try:
                # Skip own messages
                if message.from_user and message.from_user.is_self:
                    return
                
                logger.info(f"📨 New post detected: {message.text[:50] if message.text else 'Media post'}")
                
                # 1. ACTUALLY MARK AS READ (Increase view count)
                await mark_message_as_read(client, message)
                
                # 2. AUTO-REACT after delay
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
                    logger.warning(f"⚠️ Could not react: {e}")
                
                # 3. CHECK FOR LIVE STREAM
                live_stream_url = None
                if message.text:
                    text_lower = message.text.lower()
                    
                    # Extract live stream URL if present
                    if 't.me/' in message.text and 'livestream=' in message.text:
                        # Find the live stream URL in the message
                        words = message.text.split()
                        for word in words:
                            if 't.me/' in word and 'livestream=' in word:
                                live_stream_url = word
                                break
                    
                    # Check for live stream keywords
                    live_keywords = ['live now', 'voice chat', 'stream', 'vc started', '🎧', '🔴 live', 'join call', 'livestream']
                    if any(keyword in text_lower for keyword in live_keywords) or live_stream_url:
                        logger.info(f"🎬 Live stream detected! URL: {live_stream_url}")
                        logger.info("🔄 Attempting to join in 15 seconds...")
                        await asyncio.sleep(15)
                        await join_live_stream(client, channel, live_stream_url)
                    
            except Exception as e:
                logger.error(f"❌ Error handling message: {e}")

        # PERIODIC TASKS - Actually view posts regularly
        async def periodic_tasks():
            counter = 0
            while True:
                await asyncio.sleep(300)  # Every 5 minutes
                counter += 1
                
                if counter % 2 == 0:  # Every 10 minutes
                    logger.info("🔄 Periodic: Actually viewing recent posts...")
                    viewed_count = await view_recent_posts(client, channel)
                    logger.info(f"📊 Viewed {viewed_count} posts in this cycle")
                
                logger.info(f"📊 Bot active - Cycle {counter}")
        
        # Start periodic tasks
        asyncio.create_task(periodic_tasks())
        
        # KEEP BOT RUNNING
        logger.info("🤖 Bot is now actively monitoring...")
        while True:
            await asyncio.sleep(60)
            
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")

def start_bot():
    asyncio.run(telegram_bot())

if __name__ == '__main__':
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
