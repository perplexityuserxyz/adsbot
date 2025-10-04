from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from utils import get_user_groups_from_account
import logging

logger = logging.getLogger(__name__)

class AdHandler:
    def __init__(self, bot: Client, db: Database, user_manager):
        self.bot = bot
        self.db = db
        self.user_manager = user_manager
        self.ad_setup_state = {}
    
    async def start_ad_setup(self, message: Message):
        """Start ad setup process"""
        user_id = message.from_user.id
        self.ad_setup_state[user_id] = "awaiting_ad"
        await message.reply_text(
            "📢 **Set Your Advertisement**\n\n"
            "Send me your advertisement. You can send:\n"
            "• Text message\n"
            "• Photo with caption\n"
            "• Video with caption\n\n"
            "Send /cancel to cancel."
        )
    
    async def handle_ad_message(self, message: Message):
        """Handle incoming ad message"""
        user_id = message.from_user.id
        
        if user_id not in self.ad_setup_state:
            return
        
        try:
            ad_text = message.text or message.caption or ""
            media_type = None
            media_file_id = None
            
            if message.photo:
                media_type = "photo"
                media_file_id = message.photo.file_id
            elif message.video:
                media_type = "video"
                media_file_id = message.video.file_id
            
            if not ad_text and not media_file_id:
                await message.reply_text("❌ Please send a valid advertisement.")
                return
            
            # Save ad
            self.db.save_ad(user_id, ad_text, media_type, media_file_id)
            
            # Remove state
            del self.ad_setup_state[user_id]
            
            await message.reply_text(
                "✅ **Advertisement Saved!**\n\n"
                "Your ad has been saved successfully.\n\n"
                "📝 Next steps:\n"
                "• Add groups: /addgroups\n"
                "• Start automation: /start_ads"
            )
            
        except Exception as e:
            logger.error(f"Error saving ad: {e}")
            await message.reply_text(f"❌ Error saving ad: {str(e)}")

class GroupHandler:
    def __init__(self, bot: Client, db: Database, user_manager):
        self.bot = bot
        self.db = db
        self.user_manager = user_manager
    
    async def add_groups_command(self, message: Message):
        """Handle add groups command"""
        user_id = message.from_user.id
        user = self.db.get_user(user_id)
        
        if not user or not user['session_string']:
            await message.reply_text("❌ Please login first with /login")
            return
        
        user_client = self.user_manager.active_sessions.get(user_id)
        if not user_client:
            await message.reply_text("❌ Session not active. Please try /login again.")
            return
        
        await message.reply_text("🔍 **Fetching your groups...**\n\nPlease wait...")
        
        try:
            groups = await get_user_groups_from_account(user_client)
            
            if not groups:
                await message.reply_text("❌ No groups found in your account.")
                return
            
            # Save all groups
            for group in groups:
                self.db.add_group(user_id, group['id'], group['title'])
            
            groups_list = "\n".join([f"• {g['title']}" for g in groups[:20]])
            
            await message.reply_text(
                f"✅ **Groups Added Successfully!**\n\n"
                f"Total groups: {len(groups)}\n\n"
                f"**Groups:**\n{groups_list}\n\n"
                f"{'...' if len(groups) > 20 else ''}\n\n"
                f"Use /listgroups to see all groups.\n"
                f"Use /start_ads to begin forwarding!"
            )
            
        except Exception as e:
            logger.error(f"Error fetching groups: {e}")
            await message.reply_text(f"❌ Error fetching groups: {str(e)}")
    
    async def list_groups_command(self, message: Message):
        """List all user groups"""
        user_id = message.from_user.id
        groups = self.db.get_user_groups(user_id)
        
        if not groups:
            await message.reply_text("❌ No groups added yet. Use /addgroups to add groups.")
            return
        
        groups_text = "👥 **Your Groups:**\n\n"
        for i, group in enumerate(groups, 1):
            groups_text += f"{i}. {group['group_name']}\n"
        
        groups_text += f"\n📊 Total: {len(groups)} groups"
        
        await message.reply_text(groups_text)

class AutomationHandler:
    def __init__(self, bot: Client, db: Database, user_manager):
        self.bot = bot
        self.db = db
        self.user_manager = user_manager
    
    async def start_ads_command(self, message: Message):
        """Start automation"""
        user_id = message.from_user.id
        user = self.db.get_user(user_id)
        
        if not user or not user['session_string']:
            await message.reply_text("❌ Please login first with /login")
            return
        
        # Check if ad is set
        ad = self.db.get_active_ad(user_id)
        if not ad:
            await message.reply_text("❌ Please set your ad first with /setad")
            return
        
        # Check if groups added
        groups = self.db.get_user_groups(user_id)
        if not groups:
            await message.reply_text("❌ Please add groups first with /addgroups")
            return
        
        # Start automation
        self.db.set_user_active(user_id, True)
        await self.user_manager.start_automation(user_id)
        
        delay_text = f"{user['delay_seconds']} seconds ({user['delay_seconds']//60} minutes)"
        
        await message.reply_text(
            f"✅ **Automation Started!**\n\n"
            f"Your ads will be forwarded to {len(groups)} groups every {delay_text}.\n\n"
            f"📊 Check /status for statistics\n"
            f"🛑 Use /stop_ads to stop automation"
        )
    
    async def stop_ads_command(self, message: Message):
        """Stop automation"""
        user_id = message.from_user.id
        
        self.db.set_user_active(user_id, False)
        await self.user_manager.stop_automation(user_id)
        
        await message.reply_text(
            "🛑 **Automation Stopped!**\n\n"
            "Your ad forwarding has been stopped.\n\n"
            "Use /start_ads to resume."
        )

class DelayHandler:
    def __init__(self, bot: Client, db: Database):
        self.bot = bot
        self.db = db
    
    async def delay_command(self, message: Message):
        """Handle delay command"""
        user_id = message.from_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            await message.reply_text("❌ User not found. Use /start first.")
            return
        
        is_premium = user['is_premium']
        
        if not is_premium:
            await message.reply_text(
                "❌ **Premium Feature**\n\n"
                "Custom delay is only available for premium users.\n"
                "Free users have a fixed 5-minute delay.\n\n"
                "Upgrade to premium: /plans"
            )
            return
        
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply_text(
                f"⏱️ **Current Delay:** {user['delay_seconds']} seconds\n\n"
                f"**Usage:** /delay <seconds>\n"
                f"Example: /delay 30\n\n"
                f"**Limits:**\n"
                f"• Minimum: 10 seconds\n"
                f"• Maximum: 600 seconds (10 minutes)"
            )
            return
        
        try:
            delay = int(args[1])
            
            if delay < 10 or delay > 600:
                await message.reply_text(
                    "❌ Invalid delay. Must be between 10 and 600 seconds."
                )
                return
            
            self.db.update_user_delay(user_id, delay)
            
            await message.reply_text(
                f"✅ **Delay Updated!**\n\n"
                f"New delay: {delay} seconds ({delay//60} minutes)"
            )
            
        except ValueError:
            await message.reply_text("❌ Invalid delay. Please enter a number.")

class UpgradeHandler:
    def __init__(self, bot: Client, db: Database):
        self.bot = bot
        self.db = db
        self.upgrade_state = {}
    
    async def upgrade_command(self, message: Message):
        """Handle upgrade command"""
        user_id = message.from_user.id
        
        from config import PRICING
        
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            plans_text = "💎 **Choose Your Plan:**\n\n"
            for plan_id, plan_info in PRICING.items():
                plans_text += f"**{plan_info['name']}** - ₹{plan_info['price']}/month\n"
            
            plans_text += "\n**Usage:** /upgrade <plan_name>\n"
            plans_text += "Example: /upgrade basic"
            
            await message.reply_text(plans_text)
            return
        
        plan_type = args[1].lower()
        
        if plan_type not in PRICING:
            await message.reply_text(
                "❌ Invalid plan. Choose from: basic, pro, unlimited"
            )
            return
        
        plan_info = PRICING[plan_type]
        
        payment_text = f"""
💎 **Upgrade to {plan_info['name']}**

💰 Price: ₹{plan_info['price']}
⏰ Duration: {plan_info['duration_days']} days

**Payment Instructions:**
1. Send ₹{plan_info['price']} to:
   UPI: yourpaymentid@upi (Change this)
   
2. Take a screenshot of payment
3. Send the screenshot here

After sending screenshot, your payment will be reviewed by admin.
        """
        
        self.upgrade_state[user_id] = {
            'plan': plan_type,
            'amount': plan_info['price'],
            'awaiting_proof': True
        }
        
        await message.reply_text(payment_text)
    
    async def handle_payment_proof(self, message: Message):
        """Handle payment proof screenshot"""
        user_id = message.from_user.id
        
        if user_id not in self.upgrade_state:
            return
        
        if not message.photo:
            await message.reply_text("❌ Please send a screenshot of your payment.")
            return
        
        upgrade_data = self.upgrade_state[user_id]
        
        # Save payment request
        payment_id = self.db.create_payment_request(
            user_id,
            upgrade_data['plan'],
            upgrade_data['amount'],
            message.photo.file_id
        )
        
        del self.upgrade_state[user_id]
        
        await message.reply_text(
            f"✅ **Payment Submitted!**\n\n"
            f"Your payment proof has been submitted for review.\n"
            f"Payment ID: #{payment_id}\n\n"
            f"Admin will verify and activate your premium within 24 hours.\n"
            f"You'll receive a notification once approved."
        )
        
        # Notify owner
        from config import OWNER_ID
        await self.bot.send_photo(
            OWNER_ID,
            message.photo.file_id,
            caption=f"💰 **New Payment Request**\n\n"
                    f"User ID: {user_id}\n"
                    f"Plan: {upgrade_data['plan']}\n"
                    f"Amount: ₹{upgrade_data['amount']}\n"
                    f"Payment ID: #{payment_id}\n\n"
                    f"Use /approve {payment_id} to approve"
        )
