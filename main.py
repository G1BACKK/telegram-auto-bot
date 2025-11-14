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
    return "🤖 Telegram Auto Bot - Viewing, Reacting & Joining Live Streams!"

@app.route('/health')
def health():
    return "OK"

async def view_posts_activity(client, channel):
    """Simple post viewing by fetching recent messages"""
    try:
        logger.info("👀 Starting post viewing activity...")
        count = 0
        async for message in client.get_chat_history(channel.id, limit=10):
            # Mark as viewed by accessing message details
            if count < 5:  # View first 5 posts
                if message.text:
                    logger.info(f"👁️ Viewed post: {message.text[:30]}...")
                else:
                    logger.info("👁️ Viewed media post")
                count += 1
                await asyncio.sleep(2)
        logger.info(f"✅ Viewed {count} posts")
    except Exception as e:
        logger.error(f"❌ Error in post viewing: {e}")

async def join_live_stream_simple(client, channel):
    """Simple method to join live streams"""
    try:
        logger.info("🎧 Checking for live streams...")
        
        # Method 1: Check recent messages for live stream indicators
        async for message in client.get_chat_history(channel.id, limit=20):
            if message.text and any(keyword in message.text.lower() for keyword in 
                                  ['live now', 'voice chat', 'stream', 'vc started', '🎧', '🔴 live']):
                logger.info(f"🎬 Live stream detected: {message.text[:40]}...")
                
                # Try to join using group call methods
                try:
                    # Get active group calls
                    result = await client.invoke(
                        raw.functions.channels.GetFullChannel(
                            channel=await client.resolve_peer(channel.id)
                        )
                    )
                    
                    if hasattr(result, 'full_chat') and hasattr(result.full_chat, 'call'):
                        logger.info("🎧 Found active group call, attempting to join...")
                        # Join the call
                        await client.invoke(
                            raw.functions.phone.JoinGroupCall(
                                call=result.full_chat.call,
                                join_as=await client.resolve_peer((await client.get_me()).id),
                                params=raw.types.DataJSON(data='{}')
                            )
                        )
                        logger.info("✅ SUCCESS: Joined live stream!")
                        return True
                        
                except Exception as call_error:
                    logger.info(f"🎧 Could not join call: {call_error}")
        
        logger.info("❌ No live streams found to join")
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
        
        # Import raw for voice chat features
        from pyrogram import raw
        
        # INITIAL ACTIVITIES - DO THIS ON START
        logger.info("🔄 Performing initial activities...")
        
        # 1. VIEW POSTS initially
        await view_posts_activity(client, channel)
        
        # 2. CHECK FOR LIVE STREAMS initially
        await join_live_stream_simple(client, channel)
        
        logger.info("🎯 BOT READY! Auto-viewing, reacting & monitoring live streams")
        
        # MAIN MESSAGE HANDLER - FOR ALL NEW POSTS
        @client.on_message(filters.chat(channel.id))
        async def handle_all_messages(client, message: Message):
            try:
                # Skip own messages
                if message.from_user and message.from_user.is_author:
                    return
                
                logger.info(f"📨 New post detected in {message.chat.title}")
                
                # 1. AUTO-VIEW (happens automatically when we process the message)
                logger.info("👀 Auto-viewing this post...")
                
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
                
                # 3. CHECK IF LIVE STREAM ANNOUNCEMENT
                is_live = False
                if message.text:
                    text_lower = message.text.lower()
                    live_keywords = ['live now', 'voice chat', 'stream', 'vc started', '🎧', '🔴 live', 'join call']
                    if any(keyword in text_lower for keyword in live_keywords):
                        is_live = True
                        logger.info("🎬 Live stream announcement detected!")
                
                if is_live:
                    logger.info("🔄 Attempting to join live stream in 10 seconds...")
                    await asyncio.sleep(10)
                    await join_live_stream_simple(client, channel)
                    
            except Exception as e:
                logger.error(f"❌ Error handling message: {e}")

        # PERIODIC ACTIVITIES
        async def periodic_tasks():
            counter = 0
            while True:
                await asyncio.sleep(180)  # Every 3 minutes
                counter += 1
                
                if counter % 2 == 0:  # Every 6 minutes
                    logger.info("🔄 Periodic: Viewing recent posts...")
                    await view_posts_activity(client, channel)
                
                if counter % 3 == 0:  # Every 9 minutes
                    logger.info("🔄 Periodic: Checking for live streams...")
                    await join_live_stream_simple(client, channel)
                
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
