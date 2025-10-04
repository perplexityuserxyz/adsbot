#!/usr/bin/env python3
"""
Telegram Ads Forwarding BOT
Main entry point with all handlers integrated
"""

import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import logging

from config import *
from database import Database
from user_client import UserClientManager
from handlers import AdHandler, GroupHandler, AutomationHandler, DelayHandler, UpgradeHandler
from admin_handlers import AdminHandler
from utils import check_channel_membership

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = Client(
    "ads_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Initialize database
db = Database()

# Initialize user client manager
user_manager = UserClientManager(bot, db)

# Initialize handlers
ad_handler = AdHandler(bot, db, user_manager)
group_handler = GroupHandler(bot, db, user_manager)
automation_handler = AutomationHandler(bot, db, user_manager)
delay_handler = DelayHandler(bot, db)
upgrade_handler = UpgradeHandler(bot, db)
admin_handler = AdminHandler(bot, db, user_manager, OWNER_ID)

# ============ BOT COMMANDS ============

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Add user to database
    db.add_user(user_id, username)
    
    # Check channel membership
    if not await check_channel_membership(client, user_id, FORCE_JOIN_CHANNEL):
        await message.reply_text(
            f"⚠️ **Please join our main channel first!**\n\n"
            f"Join: {FORCE_JOIN_CHANNEL}\n\n"
            f"After joining, send /start again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_JOIN_CHANNEL.replace('@', '')}")]
            ])
        )
        return
    
    user = db.get_user(user_id)
    
    welcome_text = f"""
🤖 **Welcome to Telegram Ads Forwarding BOT!**

👤 User: {username or 'User'}
📊 Status: {'🌟 Premium' if user and user['is_premium'] else '🆓 Free'}

**Available Commands:**

🔐 **Account:**
/login - Login with your account
/status - Check your status

📢 **Ads:**
/setad - Set advertisement
/viewad - View current ad

👥 **Groups:**
/addgroups - Add groups
/listgroups - List groups

⚙️ **Automation:**
/start_ads - Start forwarding
/stop_ads - Stop forwarding

💎 **Premium:**
/plans - View plans
/upgrade - Upgrade account
/delay - Set delay (Premium)

❓ /help - Full command list
    """
    
    await message.reply_text(welcome_text)

@bot.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    help_text = """
📖 **Complete Command Guide**

**🔐 Account Management:**
/login - Login with Telegram session
/logout - Logout from bot
/status - Check status & statistics

**📢 Advertisement:**
/setad - Set your advertisement
/viewad - View current ad

**👥 Group Management:**
/addgroups - Auto-add all your groups
/listgroups - View all added groups
/removegroup - Remove specific group

**⚙️ Automation Control:**
/start_ads - Start automatic forwarding
/stop_ads - Stop automatic forwarding

**💎 Premium Features:**
/delay - Set custom delay (Premium only)
/plans - View all premium plans
/upgrade - Upgrade to premium

**👨‍💼 Admin Commands:**
/stats - Bot statistics
/payments - Pending payments
/approve - Approve payment
/reject - Reject payment
/ownerads - Save promotional ad
/broadcast - Broadcast owner ad
/broadcasttext - Broadcast message

**Features:**
✅ Auto log channel creation
✅ Mention notifications
✅ Bio/Name lock (Free tier)
✅ Custom delays (Premium)
✅ Multiple group support
    """
    await message.reply_text(help_text)

@bot.on_message(filters.command("login") & filters.private)
async def login_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not await check_channel_membership(client, user_id, FORCE_JOIN_CHANNEL):
        await message.reply_text(f"⚠️ Please join {FORCE_JOIN_CHANNEL} first!")
        return
    
    user = db.get_user(user_id)
    if user and user['session_string']:
        await message.reply_text(
            "✅ You're already logged in!\n\n"
            "Use /logout to logout and login again."
        )
        return
    
    login_text = """
🔐 **Login to Your Telegram Account**

**How it works:**
1. You send your phone number
2. Telegram sends you an OTP code
3. You enter the code here
4. Your session is saved securely

**Security:**
✅ Session stored encrypted
✅ We never access your messages
✅ Logout anytime with /logout

**Ready?** Send your phone number with country code.
Example: +1234567890

Send /cancel to cancel.
    """
    
    await message.reply_text(login_text)
    user_manager.login_states[user_id] = "awaiting_phone"

@bot.on_message(filters.command("logout") & filters.private)
async def logout_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Stop automation
    db.set_user_active(user_id, False)
    await user_manager.stop_automation(user_id)
    
    # Disconnect session
    if user_id in user_manager.active_sessions:
        try:
            await user_manager.active_sessions[user_id].stop()
            del user_manager.active_sessions[user_id]
        except:
            pass
    
    # Remove from database
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET session_string = NULL, is_active = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    await message.reply_text(
        "✅ **Logged Out Successfully!**\n\n"
        "Your session has been removed.\n"
        "Use /login to login again."
    )

@bot.on_message(filters.command("status") & filters.private)
async def status_command(client: Client, message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.reply_text("❌ User not found. Use /start first.")
        return
    
    if not user['session_string']:
        await message.reply_text("❌ Not logged in. Use /login to get started.")
        return
    
    groups = db.get_user_groups(user_id)
    ad = db.get_active_ad(user_id)
    
    from datetime import datetime
    is_premium = user['is_premium'] and user['subscription_expires'] and \
                 datetime.fromisoformat(user['subscription_expires']) > datetime.now()
    
    status_text = f"""
📊 **Your Status**

👤 **Account:**
• Phone: {user['phone_number']}
• Tier: {'🌟 Premium' if is_premium else '🆓 Free'}

📢 **Ad:** {'✅ Set' if ad else '❌ Not set'}
👥 **Groups:** {len(groups)}
⚙️ **Automation:** {'🟢 Running' if user['is_active'] else '🔴 Stopped'}
⏱️ **Delay:** {user['delay_seconds']}s

📈 **Subscription:**
    """
    
    if is_premium:
        expires = datetime.fromisoformat(user['subscription_expires'])
        days_left = (expires - datetime.now()).days
        status_text += f"• Expires: {expires.strftime('%Y-%m-%d')}\n• Days left: {days_left}"
    else:
        status_text += "• Free tier (5 min delay)\n• Upgrade: /plans"
    
    await message.reply_text(status_text)

# Ad commands
@bot.on_message(filters.command("setad") & filters.private)
async def setad_command(client: Client, message: Message):
    user = db.get_user(message.from_user.id)
    if not user or not user['session_string']:
        await message.reply_text("❌ Please login first: /login")
        return
    await ad_handler.start_ad_setup(message)

@bot.on_message(filters.command("viewad") & filters.private)
async def viewad_command(client: Client, message: Message):
    ad = db.get_active_ad(message.from_user.id)
    if not ad:
        await message.reply_text("❌ No ad set. Use /setad to create one.")
        return
    
    if ad['media_type'] and ad['media_file_id']:
        if ad['media_type'] == 'photo':
            await message.reply_photo(ad['media_file_id'], caption=ad['ad_text'])
        elif ad['media_type'] == 'video':
            await message.reply_video(ad['media_file_id'], caption=ad['ad_text'])
    else:
        await message.reply_text(f"📢 **Your Ad:**\n\n{ad['ad_text']}")

# Group commands
@bot.on_message(filters.command("addgroups") & filters.private)
async def addgroups_command(client: Client, message: Message):
    await group_handler.add_groups_command(message)

@bot.on_message(filters.command("listgroups") & filters.private)
async def listgroups_command(client: Client, message: Message):
    await group_handler.list_groups_command(message)

# Automation commands
@bot.on_message(filters.command("start_ads") & filters.private)
async def start_ads_command(client: Client, message: Message):
    await automation_handler.start_ads_command(message)

@bot.on_message(filters.command("stop_ads") & filters.private)
async def stop_ads_command(client: Client, message: Message):
    await automation_handler.stop_ads_command(message)

# Premium commands
@bot.on_message(filters.command("delay") & filters.private)
async def delay_command(client: Client, message: Message):
    await delay_handler.delay_command(message)

@bot.on_message(filters.command("plans") & filters.private)
async def plans_command(client: Client, message: Message):
    plans_text = """
💎 **Premium Plans**

**🆓 Free Plan:**
• Unlimited groups
• 5 minutes delay
• Forced footer
• Owner ads enabled
• Bio/Name locked

**💰 Basic - ₹199/month:**
• Unlimited groups
• 10s - 10min delay
• No footer
• No owner ads
• Free bio/name

**🚀 Pro - ₹399/month:**
• All Basic features
• Priority support
• Advanced analytics

**⭐ Unlimited - ₹599/month:**
• All Pro features
• Fastest forwarding
• Dedicated support

**Upgrade:** /upgrade <plan>
    """
    await message.reply_text(plans_text)

@bot.on_message(filters.command("upgrade") & filters.private)
async def upgrade_command(client: Client, message: Message):
    await upgrade_handler.upgrade_command(message)

# Admin commands
@bot.on_message(filters.command("stats") & filters.private & filters.user(OWNER_ID))
async def stats_command(client: Client, message: Message):
    await admin_handler.stats_command(message)

@bot.on_message(filters.command("payments") & filters.private & filters.user(OWNER_ID))
async def payments_command(client: Client, message: Message):
    await admin_handler.payments_command(message)

@bot.on_message(filters.command("approve") & filters.private & filters.user(OWNER_ID))
async def approve_command(client: Client, message: Message):
    await admin_handler.approve_command(message)

@bot.on_message(filters.command("reject") & filters.private & filters.user(OWNER_ID))
async def reject_command(client: Client, message: Message):
    await admin_handler.reject_command(message)

@bot.on_message(filters.command("ownerads") & filters.private & filters.user(OWNER_ID))
async def ownerads_command(client: Client, message: Message):
    await admin_handler.ownerads_command(message)

@bot.on_message(filters.command("broadcast") & filters.private & filters.user(OWNER_ID))
async def broadcast_command(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("Usage: /broadcast <ad_id>")
        return
    
    try:
        ad_id = int(args[1])
        await message.reply_text(f"🚀 Broadcasting ad #{ad_id}...")
        await user_manager.broadcast_owner_ad(ad_id)
        await message.reply_text("✅ Broadcast completed!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@bot.on_message(filters.command("broadcasttext") & filters.private & filters.user(OWNER_ID))
async def broadcasttext_command(client: Client, message: Message):
    await admin_handler.broadcast_text_command(message)

# Message handler for flows
@bot.on_message(filters.private & ~filters.command([]))
async def message_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Handle login flow
    if user_id in user_manager.login_states:
        await user_manager.handle_login_flow(message)
        return
    
    # Handle ad setup
    if user_id in ad_handler.ad_setup_state:
        await ad_handler.handle_ad_message(message)
        return
    
    # Handle owner ad setup
    if user_id in admin_handler.owner_ad_state:
        await admin_handler.handle_owner_ad(message)
        return
    
    # Handle payment proof
    if user_id in upgrade_handler.upgrade_state and message.photo:
        await upgrade_handler.handle_payment_proof(message)
        return

# Main function
async def main():
    logger.info("=" * 50)
    logger.info("🤖 Starting Telegram Ads Forwarding BOT")
    logger.info("=" * 50)
    
    # Create sessions directory
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    logger.info(f"📁 Sessions directory: {SESSIONS_DIR}")
    
    # Start bot
    logger.info("🔄 Starting bot client...")
    await bot.start()
    logger.info(f"✅ Bot started: @{(await bot.get_me()).username}")
    
    # Start user client manager
    logger.info("🔄 Loading user sessions...")
    await user_manager.start()
    logger.info(f"✅ Loaded {len(user_manager.active_sessions)} active sessions")
    
    logger.info("=" * 50)
    logger.info("🎉 BOT IS READY!")
    logger.info("=" * 50)
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        bot.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
