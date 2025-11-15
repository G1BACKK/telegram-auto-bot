import os
import asyncio
import random
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.tl.functions.phone import JoinGroupCallRequest
from telethon.tl.types import InputGroupCall
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

async def join_live_stream_telethon(client, channel):
    """Join live stream using Telethon"""
    try:
        logger.info("🎧 Attempting to join live stream with Telethon...")
        
        # Get the channel entity
        entity = await client.get_entity(CHANNEL_USERNAME)
        
        # Check if there's an active group call
        full_chat = await client.get_full_entity(entity)
        
        if hasattr(full_chat, 'full_chat') and hasattr(full_chat.full_chat, 'call'):
            call = full_chat.full_chat.call
            logger.info(f"📞 Found active group call: {call}")
            
            # Join the group call
            result = await client(JoinGroupCallRequest(
                call=call,
                params=await client.invoke(GetGroupCallJoinAsRequest(
                    peer=await client.get_input_entity(entity)
                ))
            ))
            logger.info("✅ SUCCESS: Joined live stream with Telethon!")
            return True
        else:
            logger.info("❌ No active group call found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Telethon join error: {e}")
        return False

async def telegram_bot():
    # Use Telethon for better voice chat support
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    try:
        await client.start()
        me = await client.get_me()
        logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        
        # Get channel
        entity = await client.get_entity(CHANNEL_USERNAME)
        logger.info(f"✅ Monitoring channel: {entity.title}")
        
        # Join channel
        try:
            await client.join_chat(CHANNEL_USERNAME)
            logger.info("✅ Joined channel")
        except:
            logger.info("ℹ️ Already in channel")
        
        logger.info("🎯 BOT READY! Auto-viewing, reacting & live streams")
        
        # Auto-react to messages
        @client.on(events.NewMessage(chats=entity))
        async def handler(event):
            try:
                # Don't react to own messages
                if event.message.out:
                    return
                
                logger.info(f"📨 New message detected")
                
                # Mark as read (view)
                await event.message.mark_read()
                logger.info("✅ Message viewed")
                
                # React after delay
                await asyncio.sleep(random.randint(3, 8))
                reactions = ['👍', '❤️', '🔥', '⭐', '🎉']
                reaction = random.choice(reactions)
                await event.message.reply(reaction)
                logger.info(f"✅ Reacted: {reaction}")
                
                # Check for live stream
                if event.message.text and any(keyword in event.message.text.lower() for keyword in 
                                            ['live now', 'voice chat', 'stream', 'vc started']):
                    logger.info("🎬 Live stream detected - joining...")
                    await asyncio.sleep(10)
                    await join_live_stream_telethon(client, entity)
                    
            except Exception as e:
                logger.error(f"❌ Message error: {e}")
        
        # Keep running
        logger.info("🤖 Bot monitoring...")
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

def start_bot():
    asyncio.run(telegram_bot())

if __name__ == '__main__':
    from telethon.sessions import StringSession
    from telethon.tl.functions.phone import GetGroupCallJoinAsRequest
    
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
