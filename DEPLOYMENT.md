# Telegram Ads Forwarding BOT - Deployment Guide

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- VPS/Server with Ubuntu/Debian (recommended)
- Telegram Bot Token
- Telegram API ID and Hash

### Step 1: Get Required Credentials

#### 1.1 Create Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Save the **BOT_TOKEN** you receive

#### 1.2 Get API Credentials
1. Visit https://my.telegram.org/auth
2. Login with your phone number
3. Click on "API development tools"
4. Create a new application
5. Save your **API_ID** and **API_HASH**

#### 1.3 Get Your User ID
1. Open Telegram and search for `@userinfobot`
2. Send `/start`
3. Save your **User ID** (this will be OWNER_ID)

### Step 2: Server Setup

#### 2.1 Connect to Your VPS
```bash
ssh root@your_vps_ip
```

#### 2.2 Update System
```bash
apt update && apt upgrade -y
```

#### 2.3 Install Python and Dependencies
```bash
apt install python3 python3-pip git screen -y
```

### Step 3: Install Bot

#### 3.1 Clone/Upload Files
Upload all bot files to your server, or if using git:
```bash
cd /root
mkdir telegram-ads-bot
cd telegram-ads-bot
# Upload your files here
```

#### 3.2 Install Python Dependencies
```bash
pip3 install -r dependencies.txt
```

Or install manually:
```bash
pip3 install pyrogram==2.0.106 TgCrypto==1.2.5 python-dotenv==1.0.0 aiofiles==23.2.1
```

### Step 4: Configuration

#### 4.1 Create .env File
```bash
nano .env
```

#### 4.2 Add Configuration
```env
# Bot Configuration
BOT_TOKEN=your_bot_token_here
API_ID=your_api_id_here
API_HASH=your_api_hash_here

# Admin Configuration
OWNER_ID=your_telegram_user_id

# Force Join Channel (with @)
FORCE_JOIN_CHANNEL=@YourMainChannel

# Bot Username (without @)
BOT_USERNAME=YourBotUsername

# Database (optional)
DATABASE_URL=sqlite:///bot_database.db
```

Save and exit (Ctrl+X, then Y, then Enter)

### Step 5: Run the Bot

#### 5.1 Test Run
```bash
python3 main.py
```

If everything works, press Ctrl+C to stop.

#### 5.2 Run in Background (Recommended)
```bash
screen -S telegrambot
python3 main.py
```

To detach from screen: Press `Ctrl+A` then `D`

To reattach: `screen -r telegrambot`

#### 5.3 Auto-Restart on Reboot
Create a systemd service:

```bash
nano /etc/systemd/system/telegram-ads-bot.service
```

Add:
```ini
[Unit]
Description=Telegram Ads Forwarding BOT
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/telegram-ads-bot
ExecStart=/usr/bin/python3 /root/telegram-ads-bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable telegram-ads-bot
systemctl start telegram-ads-bot
```

Check status:
```bash
systemctl status telegram-ads-bot
```

View logs:
```bash
journalctl -u telegram-ads-bot -f
```

### Step 6: Configure Telegram Bot

#### 6.1 Create Force Join Channel
1. Create a new channel in Telegram
2. Make it public and set a username
3. Add your bot as admin
4. Update FORCE_JOIN_CHANNEL in .env

#### 6.2 Test the Bot
1. Open your bot in Telegram
2. Send `/start`
3. Follow the instructions

## 📋 Bot Commands

### User Commands
- `/start` - Start the bot
- `/help` - Get help
- `/login` - Login with Telegram account
- `/status` - Check bot status
- `/setad` - Set advertisement
- `/addgroups` - Add groups automatically
- `/start_ads` - Start forwarding
- `/stop_ads` - Stop forwarding
- `/plans` - View premium plans
- `/upgrade` - Upgrade to premium
- `/delay` - Set custom delay (Premium)

### Admin Commands (Owner Only)
- `/stats` - View bot statistics
- `/payments` - View pending payments
- `/approve <payment_id>` - Approve payment
- `/reject <payment_id>` - Reject payment
- `/ownerads` - Save promotional ad
- `/broadcast <ad_id>` - Broadcast owner ad
- `/broadcasttext <message>` - Broadcast text message

## 🔧 Maintenance

### View Logs
```bash
# If using screen
screen -r telegrambot

# If using systemd
journalctl -u telegram-ads-bot -f

# View log file
tail -f bot.log
```

### Restart Bot
```bash
# If using screen
screen -r telegrambot
# Press Ctrl+C, then run: python3 main.py

# If using systemd
systemctl restart telegram-ads-bot
```

### Update Bot
```bash
cd /root/telegram-ads-bot
# Upload new files
systemctl restart telegram-ads-bot
```

### Backup Database
```bash
cp bot_database.db bot_database_backup_$(date +%Y%m%d).db
```

## 🛠️ Troubleshooting

### Bot Not Starting
1. Check .env file configuration
2. Verify BOT_TOKEN is correct
3. Check Python version: `python3 --version`
4. Check logs: `journalctl -u telegram-ads-bot -n 50`

### Users Can't Login
1. Verify API_ID and API_HASH
2. Check if sessions directory exists
3. Check file permissions: `chmod -R 755 /root/telegram-ads-bot`

### Forwarding Not Working
1. Check if user session is active: `/status`
2. Verify user has set ad: `/viewad`
3. Check if groups are added: `/listgroups`
4. Check automation status: `/status`

### Premium Not Activating
1. Check payment approval: `/payments`
2. Verify user ID in payment
3. Check database for subscription_expires

## 📊 Features

### Free Tier
✅ Unlimited groups
✅ 5-minute minimum delay
✅ Forced footer on ads
✅ Owner promotional ads
✅ Bio/Name locked to bot

### Premium Tier
✅ Custom delay (10s - 10min)
✅ No forced footer
✅ No owner ads
✅ Free bio/name editing
✅ Priority support

## 🔐 Security Notes

1. Never share your .env file
2. Keep BOT_TOKEN secret
3. Regular database backups
4. Monitor bot logs
5. Use strong VPS passwords

## 💡 Tips

1. Use screen or systemd for persistence
2. Regular backups are essential
3. Monitor disk space for sessions
4. Test bot in private first
5. Read logs regularly

## 📞 Support

For issues or questions, contact the bot owner.

## 📝 License

This bot is for educational purposes. Use responsibly.
