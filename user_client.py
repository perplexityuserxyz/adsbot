import asyncio
import os
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired, FloodWait
from pyrogram.types import Message
from typing import Dict, Optional
import logging

from config import *
from database import Database

logger = logging.getLogger(__name__)

class UserClientManager:
    def __init__(self, bot: Client, db: Database):
        self.bot = bot
        self.db = db
        self.active_sessions: Dict[int, Client] = {}
        self.login_states: Dict[int, str] = {}
        self.login_data: Dict[int, Dict] = {}
        self.automation_tasks: Dict[int, asyncio.Task] = {}
        
    async def start(self):
        """Start all saved user sessions"""
        logger.info("🔄 Loading saved user sessions...")
        users = self.db.get_active_users()
        
        for user in users:
            try:
                await self.start_user_session(user['user_id'])
            except Exception as e:
                logger.error(f"Failed to start session for user {user['user_id']}: {e}")
        
        logger.info(f"✅ Loaded {len(self.active_sessions)} user sessions")
    
    async def start_user_session(self, user_id: int):
        """Start a user session from database"""
        user = self.db.get_user(user_id)
        if not user or not user['session_string']:
            return False
        
        try:
            user_client = Client(
                name=f"user_{user_id}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=user['session_string'],
                in_memory=True
            )
            
            await user_client.start()
            self.active_sessions[user_id] = user_client
            
            # Create log channel if not exists
            if not user['log_channel_id']:
                await self.create_log_channel(user_id, user_client)
            
            # Start automation if active
            if user['is_active']:
                await self.start_automation(user_id)
            
            # Setup mention handler
            await self.setup_mention_handler(user_id, user_client)
            
            # Setup bio/name lock for free users
            if not user['is_premium']:
                await self.apply_bio_name_lock(user_id, user_client)
            
            logger.info(f"✅ Started session for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting session for user {user_id}: {e}")
            return False
    
    async def create_log_channel(self, user_id: int, user_client: Client):
        """Create a private log channel for user"""
        try:
            me = await user_client.get_me()
            channel_title = f"📊 Ads Log - {me.first_name}"
            channel_description = f"Automatic forwarding logs for @{BOT_USERNAME}"
            
            channel = await user_client.create_channel(
                title=channel_title,
                description=channel_description
            )
            
            self.db.set_log_channel(user_id, channel.id)
            
            # Send welcome message to channel
            await user_client.send_message(
                channel.id,
                f"📊 **Forwarding Log Channel**\n\n"
                f"This channel will receive all forwarding reports.\n"
                f"✅ Success messages\n"
                f"❌ Error messages\n\n"
                f"Powered by @{BOT_USERNAME}"
            )
            
            logger.info(f"✅ Created log channel for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error creating log channel for user {user_id}: {e}")
    
    async def apply_bio_name_lock(self, user_id: int, user_client: Client):
        """Apply bio and name lock for free users"""
        try:
            me = await user_client.get_me()
            current_bio = me.bio or ""
            current_name = me.first_name
            
            # Lock bio
            if BOT_USERNAME not in current_bio:
                new_bio = f"{current_bio}\n\n🤖 Using @{BOT_USERNAME} for ads"
                await user_client.update_profile(bio=new_bio[:70])
            
            # Lock name (add bot mention if not present)
            if BOT_USERNAME not in current_name:
                new_name = f"{current_name} | @{BOT_USERNAME}"
                await user_client.update_profile(first_name=new_name[:64])
            
            logger.info(f"✅ Applied bio/name lock for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error applying bio/name lock for user {user_id}: {e}")
    
    async def setup_mention_handler(self, user_id: int, user_client: Client):
        """Setup handler to detect mentions in groups"""
        
        @user_client.on_message()
        async def mention_handler(client, message: Message):
            try:
                # Check if user is mentioned
                me = await client.get_me()
                if message.mentioned and message.from_user and not message.from_user.is_bot:
                    # Notify user via main bot
                    notification_text = f"""
🔔 **You were mentioned!**

👤 By: {message.from_user.first_name} (@{message.from_user.username or 'no_username'})
👥 Group: {message.chat.title if message.chat else 'Unknown'}
💬 Message: {message.text[:100] if message.text else '[Media]'}

🔗 [View Message]({message.link})
                    """
                    
                    await self.bot.send_message(user_id, notification_text)
                    
            except Exception as e:
                logger.error(f"Error in mention handler for user {user_id}: {e}")
    
    async def start_automation(self, user_id: int):
        """Start automated ad forwarding for user"""
        if user_id in self.automation_tasks:
            return
        
        task = asyncio.create_task(self.automation_loop(user_id))
        self.automation_tasks[user_id] = task
        logger.info(f"🚀 Started automation for user {user_id}")
    
    async def stop_automation(self, user_id: int):
        """Stop automated ad forwarding for user"""
        if user_id in self.automation_tasks:
            self.automation_tasks[user_id].cancel()
            del self.automation_tasks[user_id]
            logger.info(f"🛑 Stopped automation for user {user_id}")
    
    async def automation_loop(self, user_id: int):
        """Main automation loop for forwarding ads"""
        while True:
            try:
                user = self.db.get_user(user_id)
                if not user or not user['is_active']:
                    break
                
                user_client = self.active_sessions.get(user_id)
                if not user_client:
                    break
                
                # Get user's ad
                ad = self.db.get_active_ad(user_id)
                if not ad:
                    await asyncio.sleep(300)  # Wait 5 minutes if no ad
                    continue
                
                # Get user's groups
                groups = self.db.get_user_groups(user_id)
                if not groups:
                    await asyncio.sleep(300)
                    continue
                
                # Check if premium or free
                is_premium = user['is_premium']
                delay = user['delay_seconds']
                
                # Forward ad to all groups
                for group in groups:
                    try:
                        await self.forward_ad_to_group(
                            user_id, 
                            user_client, 
                            group, 
                            ad, 
                            is_premium
                        )
                        await asyncio.sleep(2)  # Small delay between groups
                        
                    except Exception as e:
                        logger.error(f"Error forwarding to group {group['group_id']}: {e}")
                        self.db.add_forwarding_log(
                            user_id, 
                            group['group_id'], 
                            group['group_name'], 
                            "failed", 
                            str(e)
                        )
                
                # Update last ad run
                self.db.update_last_ad_run(user_id)
                
                # Wait for next round
                await asyncio.sleep(delay)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in automation loop for user {user_id}: {e}")
                await asyncio.sleep(60)
    
    async def forward_ad_to_group(
        self, 
        user_id: int, 
        user_client: Client, 
        group: Dict, 
        ad: Dict, 
        is_premium: bool
    ):
        """Forward ad to a specific group"""
        try:
            # Prepare ad text
            ad_text = ad['ad_text']
            
            # Add footer for free users
            if not is_premium:
                ad_text += FREE_TIER['forced_footer']
            
            # Send message based on media type
            if ad['media_type'] and ad['media_file_id']:
                if ad['media_type'] == 'photo':
                    await user_client.send_photo(
                        group['group_id'],
                        ad['media_file_id'],
                        caption=ad_text
                    )
                elif ad['media_type'] == 'video':
                    await user_client.send_video(
                        group['group_id'],
                        ad['media_file_id'],
                        caption=ad_text
                    )
            else:
                await user_client.send_message(group['group_id'], ad_text)
            
            # Log success
            self.db.add_forwarding_log(
                user_id, 
                group['group_id'], 
                group['group_name'], 
                "success"
            )
            
            # Send log to user's channel
            user = self.db.get_user(user_id)
            if user['log_channel_id']:
                await user_client.send_message(
                    user['log_channel_id'],
                    f"✅ **Forwarded Successfully**\n\n"
                    f"📢 Group: {group['group_name']}\n"
                    f"⏰ Time: {asyncio.get_event_loop().time()}\n"
                    f"📊 Status: Success"
                )
            
        except FloodWait as e:
            logger.warning(f"FloodWait for {e.value} seconds")
            await asyncio.sleep(e.value)
            raise
        except Exception as e:
            logger.error(f"Error forwarding to group {group['group_id']}: {e}")
            raise
    
    async def broadcast_owner_ad(self, ad_id: int):
        """Broadcast owner ad through free user accounts"""
        owner_ads = self.db.get_active_owner_ads()
        owner_ad = next((ad for ad in owner_ads if ad['id'] == ad_id), None)
        
        if not owner_ad:
            logger.error(f"Owner ad {ad_id} not found")
            return
        
        free_users = self.db.get_free_users()
        
        for user in free_users:
            user_id = user['user_id']
            user_client = self.active_sessions.get(user_id)
            
            if not user_client:
                continue
            
            groups = self.db.get_user_groups(user_id)
            
            for group in groups:
                try:
                    # Send owner ad
                    ad_text = owner_ad['ad_text'] + FREE_TIER['forced_footer']
                    
                    if owner_ad['media_type'] and owner_ad['media_file_id']:
                        if owner_ad['media_type'] == 'photo':
                            await user_client.send_photo(
                                group['group_id'],
                                owner_ad['media_file_id'],
                                caption=ad_text
                            )
                    else:
                        await user_client.send_message(group['group_id'], ad_text)
                    
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Error broadcasting owner ad to group {group['group_id']}: {e}")
    
    async def handle_login_flow(self, message: Message):
        """Handle the login flow states"""
        user_id = message.from_user.id
        state = self.login_states.get(user_id)
        
        if message.text == "/cancel":
            if user_id in self.login_states:
                del self.login_states[user_id]
            if user_id in self.login_data:
                del self.login_data[user_id]
            await message.reply_text("❌ Login cancelled.")
            return
        
        if state == "awaiting_phone":
            phone = message.text.strip()
            
            try:
                # Create temporary client
                temp_client = Client(
                    name=f"temp_{user_id}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    phone_number=phone,
                    in_memory=True
                )
                
                await temp_client.connect()
                
                # Send code
                sent_code = await temp_client.send_code(phone)
                
                self.login_data[user_id] = {
                    'client': temp_client,
                    'phone': phone,
                    'phone_code_hash': sent_code.phone_code_hash
                }
                
                self.login_states[user_id] = "awaiting_code"
                
                await message.reply_text(
                    "📱 **OTP Code Sent!**\n\n"
                    "Please enter the OTP code you received.\n"
                    "Example: 12345"
                )
                
            except Exception as e:
                logger.error(f"Error sending code: {e}")
                await message.reply_text(f"❌ Error: {str(e)}\n\nPlease try again with /login")
                if user_id in self.login_states:
                    del self.login_states[user_id]
                if user_id in self.login_data:
                    del self.login_data[user_id]
        
        elif state == "awaiting_code":
            code = message.text.strip().replace(" ", "")
            login_data = self.login_data.get(user_id)
            
            if not login_data:
                await message.reply_text("❌ Session expired. Please start over with /login")
                return
            
            try:
                temp_client = login_data['client']
                
                # Try to sign in
                await temp_client.sign_in(
                    login_data['phone'],
                    login_data['phone_code_hash'],
                    code
                )
                
                # Get session string
                session_string = await temp_client.export_session_string()
                
                # Save to database
                self.db.update_user_session(user_id, session_string, login_data['phone'])
                
                await temp_client.disconnect()
                
                # Start user session
                await self.start_user_session(user_id)
                
                await message.reply_text(
                    "✅ **Login Successful!**\n\n"
                    "Your account has been connected successfully.\n\n"
                    "📝 Next steps:\n"
                    "1. Set your ad: /setad\n"
                    "2. Add groups: /addgroups\n"
                    "3. Start automation: /start_ads"
                )
                
                # Cleanup
                if user_id in self.login_states:
                    del self.login_states[user_id]
                if user_id in self.login_data:
                    del self.login_data[user_id]
                
            except SessionPasswordNeeded:
                self.login_states[user_id] = "awaiting_password"
                await message.reply_text(
                    "🔐 **2FA Password Required**\n\n"
                    "Please enter your 2FA password:"
                )
            except (PhoneCodeInvalid, PhoneCodeExpired) as e:
                await message.reply_text(
                    f"❌ Invalid or expired code.\n\nPlease try again with /login"
                )
                if user_id in self.login_states:
                    del self.login_states[user_id]
                if user_id in self.login_data:
                    del self.login_data[user_id]
            except Exception as e:
                logger.error(f"Error signing in: {e}")
                await message.reply_text(f"❌ Error: {str(e)}\n\nPlease try again with /login")
                if user_id in self.login_states:
                    del self.login_states[user_id]
                if user_id in self.login_data:
                    del self.login_data[user_id]
        
        elif state == "awaiting_password":
            password = message.text.strip()
            login_data = self.login_data.get(user_id)
            
            if not login_data:
                await message.reply_text("❌ Session expired. Please start over with /login")
                return
            
            try:
                temp_client = login_data['client']
                
                # Check password
                await temp_client.check_password(password)
                
                # Get session string
                session_string = await temp_client.export_session_string()
                
                # Save to database
                self.db.update_user_session(user_id, session_string, login_data['phone'])
                
                await temp_client.disconnect()
                
                # Start user session
                await self.start_user_session(user_id)
                
                await message.reply_text(
                    "✅ **Login Successful!**\n\n"
                    "Your account has been connected successfully.\n\n"
                    "📝 Next steps:\n"
                    "1. Set your ad: /setad\n"
                    "2. Add groups: /addgroups\n"
                    "3. Start automation: /start_ads"
                )
                
                # Cleanup
                if user_id in self.login_states:
                    del self.login_states[user_id]
                if user_id in self.login_data:
                    del self.login_data[user_id]
                
            except Exception as e:
                logger.error(f"Error with password: {e}")
                await message.reply_text(f"❌ Incorrect password.\n\nPlease try again with /login")
                if user_id in self.login_states:
                    del self.login_states[user_id]
                if user_id in self.login_data:
                    del self.login_data[user_id]
