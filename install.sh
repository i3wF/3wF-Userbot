#!/bin/bash

clear

echo "==============================="
echo " Welcome to 3wF UserBot Setup!"
echo "==============================="
echo "This script will guide you through setting up your environment and configuring your userbot."
echo ""

sleep 5

echo "Updating and upgrading packages..."
apt update -y && apt upgrade -y && echo "✔️  Packages updated and upgraded." || echo "❌ Failed to update packages."
echo ""

echo "Installing ffmpeg..."
apt install -y ffmpeg && echo "✔️  ffmpeg installed." || echo "❌ Failed to install ffmpeg."
echo ""

echo "Installing Lua..."
apt install -y lua5.3 && echo "✔️  Lua installed." || echo "❌ Failed to install Lua."
echo ""

echo "Installing Python3-venv if not installed..."
apt install -y python3-venv && echo "✔️  Python3-venv installed." || echo "❌ Failed to install Python3-venv."
echo ""

echo "Creating Python virtual environment..."
python3 -m venv myenv && source myenv/bin/activate && echo "✔️  Virtual environment created and activated." || echo "❌ Failed to create virtual environment."
echo ""

echo "Installing Python dependencies..."
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found."
    exit 1
fi
pip install -r requirements.txt && echo "✔️  Dependencies installed." || echo "❌ Failed to install dependencies."
echo ""

echo "Creating .env file if it doesn't exist..."
touch .env && echo "✔️  .env file created." || echo "❌ Failed to create .env file."
echo ""

get_env_value() {
    grep "^$1=" .env | cut -d'=' -f2
}

API_ID=$(get_env_value "API_ID")
if [ -z "$API_ID" ]; then
    echo "Enter your API ID:"
    read -r API_ID
fi
echo ""

API_HASH=$(get_env_value "API_HASH")
if [ -z "$API_HASH" ]; then
    echo "Enter your API Hash:"
    read -r API_HASH
fi
echo ""

TOKEN=$(get_env_value "TOKEN")
if [ -z "$TOKEN" ]; then
    echo "Please enter your bot token:"
    read -r TOKEN
fi
echo ""

STRING_SESSION=$(get_env_value "STRING_SESSION")
if [ -z "$STRING_SESSION" ]; then
    echo "Please enter your STRING_SESSION:"
    read -r STRING_SESSION
fi
echo ""

DB_NAME=$(get_env_value "DB_NAME")
if [ -z "$DB_NAME" ]; then
    DB_NAME="3wF"
fi

{
    echo "STRING_SESSION=$STRING_SESSION"
    echo "TOKEN=$TOKEN"
    echo "API_ID=$API_ID"
    echo "API_HASH=$API_HASH"
    echo "DB_NAME=$DB_NAME"
} > .env.tmp

if ! cmp -s .env .env.tmp; then
    mv .env.tmp .env && echo "✔️  .env file updated with new values." || echo "❌ Failed to update .env file."
else
    rm .env.tmp && echo "✔️  .env file is already up-to-date."
fi
echo ""

REPLIES_ID=$(get_env_value "REPLIES_ID")

if [ -z "$REPLIES_ID" ]; then
    echo "REPLIES_ID not found. Attempting to create a group to set it."
    export API_ID API_HASH STRING_SESSION
    python3 - <<EOF || { echo "Error creating group or saving its ID."; exit 1; }
import os
import asyncio
from pyrogram import Client
from dotenv import dotenv_values

def get_env_value(key: str, to_type, default=None):
    value = env.get(key)
    if value is None:
        return default
    try:
        return to_type(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid value for {key}: {value}") from e

env = dotenv_values("./.env")
api_id = get_env_value("API_ID", int)
api_hash = get_env_value("API_HASH", str)
session_string = get_env_value("STRING_SESSION", str)

async def main():
    async with Client('my_bot', api_id=api_id, api_hash=api_hash, session_string=session_string) as app:
        try:
            group = await app.create_group("REPLIES", [app.me.username])
            with open('.env', 'a') as f:
                f.write(f'REPLIES_ID="{group.id}"\n')
            print(f'✔️ Group created successfully with ID: {group.id}')
        except Exception as e:
            print(f"Error creating group: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())
EOF
    REPLIES_ID=$(get_env_value "REPLIES_ID")
    if [ -z "$REPLIES_ID" ]; then
        echo "❌ Failed to retrieve REPLIES_ID after attempting to create the group."
        exit 1
    else
        echo "✔️ REPLIES_ID successfully set to: $REPLIES_ID"
    fi

else
    echo "✔️  REPLIES_ID already set in .env file. Skipping group creation."
fi

if [ -z "$(get_env_value "REPLIES_ID")" ]; then
    echo "❌ .env file does not contain REPLIES_ID. Please fix the setup."
    exit 1
fi
echo ""

echo "Creating file named 3wF..."
touch 3wF && echo "✔️  File 3wF created." || echo "❌ Failed to create file 3wF."
echo ""

echo "==============================="
echo " 🎉 Setup Complete! 🎉"
echo "==============================="
echo "3wF UserBot has been successfully set up! You are now ready to run your bot."
echo ""

sleep 5

echo "==============================="
echo " Launching 3wF UserBot... 🚀"
echo "==============================="
echo "The bot will now start running. Enjoy using your custom bot!"
echo ""

python3 main.py && echo "✔️  main.py started successfully." || echo "❌ Failed to start main.py."
