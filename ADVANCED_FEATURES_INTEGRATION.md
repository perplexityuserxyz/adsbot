# 🚀 Advanced Features Integration Guide

This guide shows how to integrate the new advanced features into your bot.

## 🎯 New Features Added

### 1. 📊 Advanced Analytics & Reports
- **Commands:** `/analytics`, `/report`, `/weeklyreport`
- View detailed performance statistics
- Track success rates by group
- Daily/weekly automated reports

### 2. ⏰ Scheduled Campaigns
- **Command:** `/schedule`
- Schedule ads for specific times
- Automatic execution at scheduled time
- Multiple campaigns support

### 3. 🔄 Ad Rotation System
- **Commands:** `/myads`, `/togglead`, `/deletead`, `/autorotate`
- Manage multiple ads simultaneously
- Automatic rotation between ads
- Enable/disable specific ads

### 4. 🎯 Advanced Group Management
- **Commands:** `/pausegroup`, `/resumegroup`, `/vipgroup`, `/groupstats`
- Pause/resume specific groups
- Set group priorities (VIP groups sent first)
- View per-group performance statistics

### 5. 🎁 Referral System
- **Command:** `/referral`
- Built-in referral tracking
- Automatic rewards (free premium days)
- Shareable referral links

### 6. 📝 Ad Templates Library
- **Commands:** `/templates`, `/template`
- Pre-built ad templates
- Categories: eCommerce, Services, Events, Jobs
- Easy customization

### 7. 🔍 Session Health Monitoring
- **Command:** `/checkhealth`
- Automatic session health checks
- Early problem detection
- Recommendations for fixes

### 8. ⚡ Smart Features
- Auto-pause groups with repeated failures
- Flood wait protection improvements
- Better error handling
- Performance optimizations

## 📥 Integration Steps

### Step 1: Add New Files

Upload these files to your bot directory:
- `advanced_features.py` - Core feature implementations
- `advanced_handlers.py` - Command handlers for new features

### Step 2: Update main.py

Add imports at the top of `main.py`:

```python
from advanced_handlers import AdvancedCommandHandlers
```

After initializing other handlers, add:

```python
# Initialize advanced handlers
advanced_handlers = AdvancedCommandHandlers(bot, db, user_manager)
```

### Step 3: Add New Commands

Add these command handlers to `main.py`:

```python
# Analytics Commands
@bot.on_message(filters.command("analytics") & filters.private)
async def analytics_command(client: Client, message: Message):
    await advanced_handlers.analytics_command(message)

@bot.on_message(filters.command("report") & filters.private)
async def report_command(client: Client, message: Message):
    await advanced_handlers.report_command(message)

@bot.on_message(filters.command("weeklyreport") & filters.private)
async def weeklyreport_command(client: Client, message: Message):
    await advanced_handlers.weeklyreport_command(message)

# Ad Management Commands
@bot.on_message(filters.command("myads") & filters.private)
async def myads_command(client: Client, message: Message):
    await advanced_handlers.myads_command(message)

@bot.on_message(filters.command("togglead") & filters.private)
async def togglead_command(client: Client, message: Message):
    await advanced_handlers.togglead_command(message)

@bot.on_message(filters.command("autorotate") & filters.private)
async def autorotate_command(client: Client, message: Message):
    await advanced_handlers.autorotate_command(message)

# Group Management Commands
@bot.on_message(filters.command("pausegroup") & filters.private)
async def pausegroup_command(client: Client, message: Message):
    await advanced_handlers.pausegroup_command(message)

@bot.on_message(filters.command("resumegroup") & filters.private)
async def resumegroup_command(client: Client, message: Message):
    await advanced_handlers.resumegroup_command(message)

@bot.on_message(filters.command("vipgroup") & filters.private)
async def vipgroup_command(client: Client, message: Message):
    await advanced_handlers.vipgroup_command(message)

@bot.on_message(filters.command("groupstats") & filters.private)
async def groupstats_command(client: Client, message: Message):
    await advanced_handlers.groupstats_command(message)

# Referral Command
@bot.on_message(filters.command("referral") & filters.private)
async def referral_command(client: Client, message: Message):
    await advanced_handlers.referral_command(message)

# Template Commands
@bot.on_message(filters.command("templates") & filters.private)
async def templates_command(client: Client, message: Message):
    await advanced_handlers.templates_command(message)

@bot.on_message(filters.command("template") & filters.private)
async def template_command(client: Client, message: Message):
    await advanced_handlers.template_command(message)

# Health Check Command
@bot.on_message(filters.command("checkhealth") & filters.private)
async def checkhealth_command(client: Client, message: Message):
    await advanced_handlers.checkhealth_command(message)

# Schedule Command
@bot.on_message(filters.command("schedule") & filters.private)
async def schedule_command(client: Client, message: Message):
    await advanced_handlers.schedule_command(message)
```

### Step 4: Update Help Command

Update your help command to include new features:

```python
help_text = """
📖 **Complete Command Guide**

**🔐 Account:**
/login - Login with Telegram session
/status - Check status & statistics
/checkhealth - Check session health

**📢 Advertisement:**
/setad - Set your advertisement
/myads - View all your ads
/togglead - Enable/disable ad
/autorotate - Enable ad rotation
/templates - View ad templates

**👥 Group Management:**
/addgroups - Auto-add all your groups
/listgroups - View all groups
/pausegroup - Pause specific group
/resumegroup - Resume paused group
/vipgroup - Set group priority
/groupstats - View group statistics

**⚙️ Automation:**
/start_ads - Start forwarding
/stop_ads - Stop forwarding
/schedule - Schedule campaign

**📊 Analytics & Reports:**
/analytics - View detailed analytics
/report - Daily report
/weeklyreport - Weekly report

**💎 Premium:**
/delay - Set custom delay
/plans - View plans
/upgrade - Upgrade account

**🎁 Referral:**
/referral - View referral program

**Admin Commands:**
/stats - Bot statistics
/payments - Pending payments
/approve - Approve payment
/broadcast - Broadcast owner ad
"""
```

### Step 5: Update Start Message

Update the /start command to mention new features:

```python
welcome_text = f"""
🤖 **Welcome to Telegram Ads Forwarding BOT!**

**✨ NEW FEATURES:**
📊 Advanced Analytics
🔄 Ad Rotation
⏰ Scheduled Campaigns
🎁 Referral Program
📝 Ad Templates

**Quick Start:**
1. /login - Connect account
2. /templates - Choose ad template
3. /setad - Set your ad
4. /addgroups - Add groups
5. /start_ads - Start automation!

Type /help for all commands
"""
```

## 🎯 Feature Highlights

### Analytics Dashboard
```
/analytics - Choose time period
- View success rates
- Top performing groups
- Daily breakdown
- Export data (coming soon)
```

### Ad Rotation
```
/myads - View all ads
/togglead 1 - Toggle ad #1
/autorotate - Enable rotation
- Automatic rotation
- Equal exposure for all ads
```

### Group Management
```
/pausegroup 5 - Pause group #5
/vipgroup 3 10 - Set group #3 as VIP (priority 10)
/groupstats - View per-group performance
```

### Referral Program
```
/referral - Get your link
Rewards:
- 3 referrals = 7 days Premium
- 5 referrals = 15 days Premium
- 10 referrals = 30 days Premium
```

### Templates
```
/templates - View all templates
/template 1 - View template #1
Categories:
- eCommerce
- Services
- Events
- Jobs
```

## 🔧 Database Updates

All new tables are created automatically when you run the bot for the first time with these features.

New tables:
- `scheduled_campaigns` - Scheduled ads
- `paused_groups` - Paused group tracking
- `group_priority` - Group priorities
- `referrals` - Referral tracking
- `ad_templates` - Ad templates

## 💡 Usage Examples

### Example 1: Using Analytics
```
User: /analytics
Bot: [Shows time period options]
User: [Selects "Week"]
Bot: [Shows 7-day analytics with graphs]
```

### Example 2: Setting Up Rotation
```
User: /setad
User: [Sends Ad 1]
User: /setad
User: [Sends Ad 2]
User: /autorotate
Bot: "✅ Ad rotation enabled with 2 ads"
```

### Example 3: Managing Groups
```
User: /pausegroup
Bot: [Shows numbered group list]
User: /pausegroup 5
Bot: "✅ Group #5 paused"
```

### Example 4: Using Referral
```
User: /referral
Bot: [Shows referral link and stats]
User: [Shares link with 3 friends]
Bot: "🎉 You earned 7 days Premium!"
```

## 📊 Benefits of New Features

1. **Better Performance Tracking**
   - Know which groups perform best
   - Optimize your campaigns
   - Track success rates

2. **More Control**
   - Pause underperforming groups
   - Prioritize important groups
   - Manage multiple ads easily

3. **Growth Tools**
   - Referral system for viral growth
   - Ready-made templates for quick start
   - Scheduled campaigns for consistency

4. **User Experience**
   - Health monitoring prevents issues
   - Clear analytics for transparency
   - Professional reports

## 🚀 Next Steps

1. Upload new files to your VPS
2. Restart the bot
3. Test new commands
4. Announce new features to users
5. Monitor adoption and feedback

## 📞 Support

If you need help integrating these features:
1. Check main.py structure
2. Verify all imports
3. Check logs for errors
4. Test each feature individually

---

**Congratulations!** Your bot now has enterprise-level features! 🎉
