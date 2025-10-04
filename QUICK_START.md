# 🚀 Quick Start Guide

Get your Telegram Ads Forwarding BOT running in minutes!

## 📝 Step 1: Get Credentials (5 minutes)

### 1. Bot Token
1. Open Telegram → Search `@BotFather`
2. Send `/newbot`
3. Choose name and username
4. **Copy the token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. API Credentials
1. Visit: https://my.telegram.org/auth
2. Login with your phone number
3. Click "API development tools"
4. Create new application
5. **Copy API_ID** (number like: 12345678)
6. **Copy API_HASH** (text like: `abcdef1234567890abcdef1234567890`)

### 3. Your User ID
1. Open Telegram → Search `@userinfobot`
2. Send `/start`
3. **Copy your ID** (number like: 123456789)

### 4. Create Channel (Optional but Recommended)
1. Create a new Telegram channel
2. Make it public with username (e.g., @MyBotChannel)
3. Add your bot as admin

## 💻 Step 2: VPS Setup (10 minutes)

### Connect to VPS
```bash
ssh root@your_vps_ip
```

### Install Required Packages
```bash
# Update system
apt update && apt upgrade -y

# Install Python and tools
apt install python3 python3-pip screen -y

# Create bot directory
mkdir telegram-ads-bot
cd telegram-ads-bot
```

### Upload Bot Files
Upload all Python files to `/root/telegram-ads-bot/`:
- main.py
- bot.py
- config.py
- database.py
- user_client.py
- handlers.py
- admin_handlers.py
- utils.py
- dependencies.txt
- start.sh
- .env.example

## ⚙️ Step 3: Configure Bot (3 minutes)

### Create .env File
```bash
cp .env.example .env
nano .env
```

### Fill in Your Credentials
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
OWNER_ID=123456789
FORCE_JOIN_CHANNEL=@MyBotChannel
BOT_USERNAME=MyAwesomeBot
```

**Save and exit:** `Ctrl+X` → `Y` → `Enter`

## 🎯 Step 4: Install & Run (2 minutes)

### Install Dependencies
```bash
pip3 install pyrogram TgCrypto python-dotenv aiofiles
```

### Make Start Script Executable
```bash
chmod +x start.sh
```

### Test Run
```bash
python3 main.py
```

**If you see errors, check your .env file!**

Press `Ctrl+C` to stop.

### Run in Background
```bash
screen -S botscreen
python3 main.py
```

**To detach:** Press `Ctrl+A` then `D`
**To reattach:** `screen -r botscreen`

## 🎉 Step 5: Test Your Bot (5 minutes)

### 5.1 Start Bot
1. Open Telegram
2. Search for your bot username
3. Send `/start`
4. Join the force channel if prompted

### 5.2 Login
1. Send `/login`
2. Enter your phone number (e.g., +1234567890)
3. Enter OTP code from Telegram
4. Enter 2FA password if you have one

### 5.3 Set Advertisement
1. Send `/setad`
2. Send your ad message (text or media)
3. Wait for confirmation

### 5.4 Add Groups
1. Send `/addgroups`
2. Bot will auto-detect all your groups
3. Wait for confirmation

### 5.5 Start Automation
1. Send `/start_ads`
2. Your ads will now forward automatically!

## 📊 Quick Commands Reference

### Essential Commands
```
/start       - Start bot
/login       - Connect your account
/status      - Check status
/setad       - Set your ad
/addgroups   - Add all groups
/start_ads   - Begin automation
/stop_ads    - Stop automation
```

### Admin Commands (You Only)
```
/stats       - View statistics
/payments    - Pending payments
/approve 123 - Approve payment ID 123
/ownerads    - Save promotional ad
/broadcast 1 - Send owner ad #1
```

## 🔧 Common Issues

### Bot Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Reinstall dependencies
pip3 install pyrogram TgCrypto python-dotenv aiofiles --force-reinstall
```

### "Invalid Token" Error
- Check BOT_TOKEN in .env
- Make sure no spaces before/after
- Get new token from @BotFather

### "API ID Invalid" Error
- Check API_ID and API_HASH
- Make sure API_ID is just numbers
- Get new credentials from my.telegram.org

### Login Not Working
- Check API_ID and API_HASH
- Make sure phone number has country code
- Try logout and login again

### Can't Add Groups
- Make sure you're logged in (`/status`)
- Check if session is active
- Try `/login` again

## 💡 Pro Tips

1. **Backup Database:** `cp bot_database.db backup.db`
2. **View Logs:** `tail -f bot.log`
3. **Check if Running:** `screen -ls`
4. **Update Payment Info:** Edit `handlers.py` → `UpgradeHandler`

## 📱 Payment Setup

To receive payments, edit `handlers.py`:

Find this section:
```python
payment_text = f"""
💎 **Upgrade to {plan_info['name']}**

💰 Price: ₹{plan_info['price']}

**Payment Instructions:**
1. Send ₹{plan_info['price']} to:
   UPI: yourpaymentid@upi (Change this)  ← CHANGE THIS!
```

Replace with your payment details!

## 🎯 What's Next?

1. ✅ Bot running? Great!
2. Test with free users first
3. Set up your payment method
4. Promote your bot
5. Monitor with `/stats`

## 📞 Need Help?

- Check logs: `tail -f bot.log`
- View full guide: Read `DEPLOYMENT.md`
- Restart bot: `screen -r botscreen` → Ctrl+C → `python3 main.py`

---

**🎉 Congratulations! Your bot is ready!**

Start promoting it and earning! 💰
