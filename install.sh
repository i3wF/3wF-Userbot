#!/bin/bash

echo "==============================="
echo " Welcome to 3wF UserBot Setup!"
echo "==============================="
echo "This script will guide you through setting up your environment and configuring your userbot."
echo ""

echo "Updating and upgrading packages..."
apt update -y && apt upgrade -y

echo "Installing Python3-venv if not installed..."
apt install -y python3-venv

echo "Creating Python virtual environment..."
python3 -m venv myenv
source myenv/bin/activate

echo "Installing Python dependencies..."
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found."
    exit 1
fi
pip install -r requirements.txt

echo "Creating .env file..."
touch .env

echo "Enter your API ID:"
read -r API_ID

echo "Enter your API Hash:"
read -r API_HASH

echo "Please enter your bot token:"
read -r TOKEN

echo "Do you want to provide STRING_SESSION manually or generate it? (enter 'm' for manual or 'g' for generate)"
read -r session_choice

if [ "$session_choice" = "m" ]; then
    echo "Please enter your STRING_SESSION:"
    read -r STRING_SESSION
elif [ "$session_choice" = "g" ]; then
    echo "Generating STRING_SESSION..."
    STRING_SESSION=$(python3 -c "
from pyrogram import Client
api_id = $API_ID
api_hash = '$API_HASH'
with Client(':memory:', api_id=api_id, api_hash=api_hash) as app:
    print(app.export_session_string())
" 2>&1 | tail -n 1)
else
    echo "Invalid choice. Please enter 'm' for manual or 'g' for generate."
    exit 1
fi

echo "Saving configuration to .env file..."
{
    echo "STRING_SESSION=$STRING_SESSION"
    echo "TOKEN=$TOKEN"
    echo "API_ID=$API_ID"
    echo "API_HASH=$API_HASH"
    echo "DB_NAME=3wF"
} >> .env

echo "Creating file named 3wF..."
touch 3wF

echo "Creating required Telegram group and saving its ID..."

python3 -c "
from pyrogram import Client
import os

app = Client('my_bot', api_id=int(os.getenv('API_ID')), api_hash=os.getenv('API_HASH'), session_string=os.getenv('STRING_SESSION'))
app.start()

group = app.create_group('REPLIES')

with open('.env', 'a') as f:
    f.write(f'REPLIES_ID={group.id}\n')

app.stop()
" || { echo "Error creating groups or saving their IDs."; exit 1; }

echo "Setup complete!"
