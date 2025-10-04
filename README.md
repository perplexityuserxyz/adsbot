# Telegram Ads Forwarding BOT

A powerful Telegram bot system for automated advertisement forwarding across multiple groups with free and premium tiers.

## ✨ Features

### 🆓 Free Tier
- Unlimited group support
- 5-minute minimum forwarding delay
- Automatic log channel creation
- Mention notifications in groups
- Bio/Name branding lock
- Owner promotional ads support

### 💎 Premium Tier
- Custom delay (10 seconds - 10 minutes)
- No forced footers on ads
- No owner promotional ads
- Free bio/name editing
- Priority support
- Starting from ₹199/month

## 🚀 Key Features

- **Pyrogram-Based**: Uses Pyrogram for reliable Telegram user session management
- **Multi-Group Support**: Forward ads to unlimited groups simultaneously
- **Auto Log Channel**: Automatic creation of private log channels for each user
- **Mention Alerts**: Get notified when mentioned in any group
- **Manual Payment**: Flexible manual payment verification system
- **Owner Dashboard**: Complete admin control via Telegram commands
- **Session Management**: Secure session storage and management

## 📋 Requirements

- Python 3.8+
- VPS/Server (Ubuntu/Debian recommended)
- Telegram Bot Token
- Telegram API ID & Hash

## 🔧 Installation

### Quick Install

1. Clone or upload files to your VPS
2. Install dependencies:
   ```bash
   pip3 install -r dependencies.txt
   ```
3. Copy and configure environment:
   ```bash
   cp .env.example .env
   nano .env
   ```
4. Run the bot:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

## ⚙️ Configuration

Edit `.env` file with your credentials:

```env
BOT_TOKEN=your_bot_token
API_ID=your_api_id
API_HASH=your_api_hash
OWNER_ID=your_telegram_user_id
FORCE_JOIN_CHANNEL=@YourChannel
BOT_USERNAME=YourBotUsername
```

## 📱 Bot Commands

### User Commands
- `/start` - Initialize bot
- `/login` - Login with Telegram session
- `/setad` - Set advertisement message
- `/addgroups` - Auto-add all groups
- `/start_ads` - Begin automation
- `/stop_ads` - Stop automation
- `/status` - View statistics
- `/plans` - View premium plans
- `/upgrade` - Upgrade account

### Admin Commands
- `/stats` - Bot statistics
- `/payments` - Pending payments
- `/approve <id>` - Approve payment
- `/ownerads` - Save promotional ad
- `/broadcast <id>` - Broadcast owner ad

## 🏗️ Architecture

```
├── main.py              # Main entry point
├── bot.py               # Bot command handlers
├── config.py            # Configuration
├── database.py          # Database operations
├── user_client.py       # Pyrogram session management
├── handlers.py          # Feature handlers
├── admin_handlers.py    # Admin functions
├── utils.py             # Utility functions
└── dependencies.txt     # Python dependencies
```

## 🔐 Security

- Sessions stored securely in database
- Environment variables for sensitive data
- Owner-only admin commands
- Automatic session cleanup on logout

## 📊 Database

Uses SQLite by default. Supports PostgreSQL via `DATABASE_URL` environment variable.

**Tables:**
- `users` - User accounts and sessions
- `user_groups` - Group mappings
- `ads` - User advertisements
- `owner_ads` - Promotional ads
- `forwarding_logs` - Activity logs
- `payments` - Payment records

## 🛠️ Running in Production

### Using Screen (Simple)
```bash
screen -S telegrambot
python3 main.py
# Detach: Ctrl+A then D
# Reattach: screen -r telegrambot
```

### Using Systemd (Recommended)
```bash
sudo nano /etc/systemd/system/telegram-ads-bot.service
# Add service configuration (see DEPLOYMENT.md)
sudo systemctl enable telegram-ads-bot
sudo systemctl start telegram-ads-bot
```

## 🔄 Updates

To update the bot:
```bash
# Stop the bot
systemctl stop telegram-ads-bot

# Update files
# Upload new files

# Restart
systemctl start telegram-ads-bot
```

## 📝 Logging

Logs are written to:
- `bot.log` - File log
- Console output
- Systemd journal (if using systemd)

View logs:
```bash
tail -f bot.log
# OR
journalctl -u telegram-ads-bot -f
```

## 💡 Tips

1. Always backup `bot_database.db` regularly
2. Monitor disk space for session files
3. Test in a private environment first
4. Keep credentials secure
5. Update payment instructions in code

## ⚠️ Important Notes

- This bot uses Telegram user sessions (Pyrogram)
- Users login with their own Telegram accounts
- Ensure compliance with Telegram's Terms of Service
- Use responsibly and ethically
- Not affiliated with Telegram

## 🤝 Support

For support and questions:
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for troubleshooting
- Review bot logs for errors
- Contact bot administrator

## 📄 License

This project is for educational purposes. Use responsibly.

## 🎯 Roadmap

- [ ] PostgreSQL migration guide
- [ ] Web dashboard (optional)
- [ ] Advanced analytics
- [ ] Multi-language support
- [ ] Scheduled campaigns

---

**Made with ❤️ for Telegram automation**
