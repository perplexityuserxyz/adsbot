#!/bin/bash

# Telegram Ads Forwarding BOT - Startup Script

echo "================================================"
echo "🤖 Telegram Ads Forwarding BOT"
echo "================================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    echo ""
    echo "Run: cp .env.example .env"
    echo "Then edit .env with your configuration."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed!"
    echo "Please install Python 3.8 or higher."
    exit 1
fi

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
python3 -c "import pyrogram" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Dependencies not installed. Installing..."
    pip3 install -r dependencies.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies!"
        exit 1
    fi
    echo "✅ Dependencies installed successfully!"
fi

# Create sessions directory
if [ ! -d "sessions" ]; then
    echo "📁 Creating sessions directory..."
    mkdir -p sessions
fi

# Start the bot
echo "🚀 Starting bot..."
echo "================================================"
python3 main.py
