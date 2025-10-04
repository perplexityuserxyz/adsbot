"""
Command handlers for advanced features
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import logging

from advanced_features import (
    AnalyticsManager,
    ScheduledCampaignManager,
    AdRotationManager,
    GroupManagementFeatures,
    ReferralSystem,
    TemplateManager,
    SessionHealthMonitor,
    ReportGenerator
)

logger = logging.getLogger(__name__)

class AdvancedCommandHandlers:
    def __init__(self, bot: Client, db, user_manager):
        self.bot = bot
        self.db = db
        self.user_manager = user_manager
        
        # Initialize feature managers
        self.analytics = AnalyticsManager(db)
        self.scheduler = ScheduledCampaignManager(db)
        self.ad_rotation = AdRotationManager(db)
        self.group_mgmt = GroupManagementFeatures(db)
        self.referral = ReferralSystem(db)
        self.templates = TemplateManager(db)
        self.health_monitor = SessionHealthMonitor(db)
        self.reporter = ReportGenerator(db)
    
    # Analytics Commands
    async def analytics_command(self, message: Message):
        """Show detailed analytics"""
        user_id = message.from_user.id
        
        # Ask for time period
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Today", callback_data="analytics_1"),
                InlineKeyboardButton("Week", callback_data="analytics_7")
            ],
            [
                InlineKeyboardButton("Month", callback_data="analytics_30"),
                InlineKeyboardButton("All Time", callback_data="analytics_all")
            ]
        ])
        
        await message.reply_text(
            "📊 **Analytics Dashboard**\n\n"
            "Select time period:",
            reply_markup=keyboard
        )
    
    async def show_analytics(self, user_id: int, days: int):
        """Display analytics for period"""
        stats = self.analytics.get_user_analytics(user_id, days)
        
        period_name = {1: "Today", 7: "This Week", 30: "This Month"}.get(days, f"Last {days} Days")
        
        text = f"""
📊 **Analytics - {period_name}**

📈 **Performance:**
• Total Forwards: {stats['total_forwards']}
• Successful: {stats['successful']} ✅
• Failed: {stats['failed']} ❌
• Success Rate: {stats['success_rate']:.1f}%

🏆 **Top Performing Groups:**
"""
        
        for i, group in enumerate(stats['top_groups'][:5], 1):
            success_rate = (group['successful'] / group['forwards'] * 100) if group['forwards'] > 0 else 0
            text += f"\n{i}. **{group['name']}**\n"
            text += f"   • Total: {group['forwards']} | Success: {success_rate:.1f}%"
        
        if not stats['top_groups']:
            text += "\nNo data available yet."
        
        return text
    
    # Scheduled Campaigns
    async def schedule_command(self, message: Message):
        """Schedule an ad campaign"""
        user_id = message.from_user.id
        
        # Get user ads
        ads = self.ad_rotation.get_user_ads(user_id)
        
        if not ads:
            await message.reply_text("❌ No ads available. Create an ad first with /setad")
            return
        
        await message.reply_text(
            "📅 **Schedule Campaign**\n\n"
            "Reply with schedule time in format:\n"
            "`YYYY-MM-DD HH:MM`\n\n"
            "Example: `2024-12-25 10:30`\n\n"
            "Your ad will be sent at this time."
        )
    
    # Ad Rotation
    async def myads_command(self, message: Message):
        """List all user ads with rotation status"""
        user_id = message.from_user.id
        ads = self.ad_rotation.get_user_ads(user_id)
        
        if not ads:
            await message.reply_text(
                "❌ No ads found.\n\n"
                "Create your first ad with /setad"
            )
            return
        
        text = "📢 **Your Advertisements**\n\n"
        
        for i, ad in enumerate(ads, 1):
            status = "🟢 Active" if ad['is_active'] else "🔴 Inactive"
            text += f"{i}. {status}\n"
            text += f"   Text: {ad['ad_text'][:50]}{'...' if len(ad['ad_text']) > 50 else ''}\n"
            text += f"   Media: {ad['media_type'] or 'None'}\n"
            text += f"   ID: `{ad['id']}`\n\n"
        
        text += "\n**Commands:**\n"
        text += "• /togglead <id> - Enable/disable ad\n"
        text += "• /deletead <id> - Delete ad\n"
        text += "• /setad - Create new ad"
        
        await message.reply_text(text)
    
    async def togglead_command(self, message: Message):
        """Toggle ad active status"""
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text("Usage: /togglead <ad_id>")
            return
        
        try:
            ad_id = int(args[1])
        except:
            await message.reply_text("❌ Invalid ad ID")
            return
        
        # Get ad
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ads WHERE id = ? AND user_id = ?", 
                      (ad_id, message.from_user.id))
        ad = cursor.fetchone()
        conn.close()
        
        if not ad:
            await message.reply_text("❌ Ad not found")
            return
        
        # Toggle status
        new_status = not ad['is_active']
        self.ad_rotation.toggle_ad_status(ad_id, new_status)
        
        await message.reply_text(
            f"✅ Ad #{ad_id} is now {'🟢 Active' if new_status else '🔴 Inactive'}"
        )
    
    # Group Management
    async def pausegroup_command(self, message: Message):
        """Pause a specific group"""
        user_id = message.from_user.id
        groups = self.db.get_user_groups(user_id)
        
        if not groups:
            await message.reply_text("❌ No groups found")
            return
        
        # Show groups with numbers
        text = "⏸️ **Pause Group**\n\nSelect group to pause:\n\n"
        for i, group in enumerate(groups[:20], 1):
            paused = self.group_mgmt.is_group_paused(user_id, group['group_id'])
            status = "⏸️ Paused" if paused else "▶️ Active"
            text += f"{i}. {group['group_name']} - {status}\n"
        
        text += "\n**Usage:** /pausegroup <number>\nExample: /pausegroup 5"
        
        await message.reply_text(text)
    
    async def resumegroup_command(self, message: Message):
        """Resume a paused group"""
        user_id = message.from_user.id
        groups = self.db.get_user_groups(user_id)
        
        text = "▶️ **Resume Group**\n\nPaused groups:\n\n"
        
        paused_groups = []
        for i, group in enumerate(groups, 1):
            if self.group_mgmt.is_group_paused(user_id, group['group_id']):
                paused_groups.append((i, group))
                text += f"{i}. {group['group_name']}\n"
        
        if not paused_groups:
            await message.reply_text("✅ No paused groups")
            return
        
        text += "\n**Usage:** /resumegroup <number>"
        await message.reply_text(text)
    
    async def vipgroup_command(self, message: Message):
        """Mark group as VIP (priority)"""
        await message.reply_text(
            "⭐ **VIP Groups Feature**\n\n"
            "VIP groups are forwarded first in each cycle.\n\n"
            "**Usage:** /vipgroup <group_number> <priority>\n"
            "Priority: 1-10 (10 = highest)\n\n"
            "Example: /vipgroup 5 10\n\n"
            "View groups: /listgroups"
        )
    
    # Referral System
    async def referral_command(self, message: Message):
        """Show referral info"""
        user_id = message.from_user.id
        username = (await self.bot.get_me()).username
        
        referral_count = self.referral.get_referral_count(user_id)
        pending_rewards = self.referral.get_pending_rewards(user_id)
        
        referral_link = f"https://t.me/{username}?start=ref_{user_id}"
        
        text = f"""
🎁 **Referral Program**

📊 **Your Stats:**
• Total Referrals: {referral_count}
• Pending Rewards: {pending_rewards}

🔗 **Your Referral Link:**
`{referral_link}`

🎯 **Rewards:**
• 3 referrals = 7 days Premium FREE
• 5 referrals = 15 days Premium FREE
• 10 referrals = 30 days Premium FREE

📢 **How it works:**
1. Share your link with friends
2. They join and login
3. You earn rewards automatically!

Share now and earn Premium! 🚀
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={referral_link}")]
        ])
        
        await message.reply_text(text, reply_markup=keyboard)
    
    # Templates
    async def templates_command(self, message: Message):
        """Show ad templates"""
        templates = self.templates.get_templates()
        
        if not templates:
            await message.reply_text("❌ No templates available")
            return
        
        text = "📝 **Ad Templates**\n\n"
        text += "Choose a template to get started:\n\n"
        
        categories = {}
        for template in templates:
            cat = template['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(template)
        
        for category, tmps in categories.items():
            text += f"\n**{category.upper()}:**\n"
            for tmp in tmps:
                text += f"• {tmp['name']} - `/template {tmp['id']}`\n"
        
        text += "\n\n**Usage:** /template <id> to view template"
        
        await message.reply_text(text)
    
    async def template_command(self, message: Message):
        """View a specific template"""
        args = message.text.split()
        if len(args) < 2:
            await self.templates_command(message)
            return
        
        try:
            template_id = int(args[1])
        except:
            await message.reply_text("❌ Invalid template ID")
            return
        
        # Get template
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ad_templates WHERE id = ?", (template_id,))
        template = cursor.fetchone()
        conn.close()
        
        if not template:
            await message.reply_text("❌ Template not found")
            return
        
        text = f"""
📝 **Template: {template['name']}**

**Category:** {template['category']}

**Template Text:**
{template['template_text']}

**Note:** Replace {'{variable}'} with your content

**To use:** Copy the text, replace variables, and send with /setad
        """
        
        await message.reply_text(text)
    
    # Reports
    async def report_command(self, message: Message):
        """Generate daily report"""
        user_id = message.from_user.id
        report = self.reporter.generate_daily_report(user_id)
        await message.reply_text(report)
    
    async def weeklyreport_command(self, message: Message):
        """Generate weekly report"""
        user_id = message.from_user.id
        report = self.reporter.generate_weekly_report(user_id)
        await message.reply_text(report)
    
    # Session Health
    async def checkhealth_command(self, message: Message):
        """Check session health"""
        user_id = message.from_user.id
        user_client = self.user_manager.active_sessions.get(user_id)
        
        if not user_client:
            await message.reply_text(
                "❌ **Session Not Active**\n\n"
                "Please login first: /login"
            )
            return
        
        await message.reply_text("🔍 Checking session health...")
        
        health = await self.health_monitor.check_session_health(user_id, user_client)
        
        if health['is_healthy']:
            text = "✅ **Session Healthy**\n\nAll systems operational!"
        else:
            text = "⚠️ **Session Issues Detected**\n\n"
            text += "**Issues:**\n"
            for issue in health['issues']:
                text += f"❌ {issue}\n"
        
        if health['warnings']:
            text += "\n**Warnings:**\n"
            for warning in health['warnings']:
                text += f"⚠️ {warning}\n"
        
        text += "\n\nRecommendation: "
        if not health['is_healthy']:
            text += "Try /logout and /login again"
        else:
            text += "Everything looks good!"
        
        await message.reply_text(text)
    
    # Group Stats
    async def groupstats_command(self, message: Message):
        """Show stats for a specific group"""
        user_id = message.from_user.id
        groups = self.db.get_user_groups(user_id)
        
        if not groups:
            await message.reply_text("❌ No groups found")
            return
        
        text = "📊 **Group Statistics**\n\n"
        text += "Select a group to view detailed stats:\n\n"
        
        for i, group in enumerate(groups[:20], 1):
            perf = self.analytics.get_group_performance(user_id, group['group_id'])
            text += f"{i}. {group['group_name']}\n"
            text += f"   Success: {perf['success_rate']:.1f}% ({perf['successful']}/{perf['total_forwards']})\n\n"
        
        text += "**Usage:** /groupstats <number> for details"
        
        await message.reply_text(text)
    
    # Auto-rotate ads feature
    async def autorotate_command(self, message: Message):
        """Enable/disable ad rotation"""
        user_id = message.from_user.id
        ads = self.ad_rotation.get_user_ads(user_id)
        
        if len(ads) < 2:
            await message.reply_text(
                "⚠️ **Ad Rotation**\n\n"
                "You need at least 2 active ads to use rotation.\n"
                f"Current ads: {len(ads)}\n\n"
                "Create more ads with /setad"
            )
            return
        
        text = f"""
🔄 **Ad Rotation Enabled**

You have {len(ads)} active ads that will be rotated automatically.

**How it works:**
• Each forwarding cycle uses a different ad
• Ads rotate in round-robin fashion
• All ads get equal exposure

**Active Ads:**
"""
        
        for i, ad in enumerate(ads, 1):
            text += f"{i}. {ad['ad_text'][:40]}...\n"
        
        text += "\n**Commands:**\n"
        text += "• /myads - Manage ads\n"
        text += "• /togglead - Enable/disable specific ad"
        
        await message.reply_text(text)
