from pyrogram import Client
import asyncio

API_ID = int(input("Please enter your API ID: "))
API_HASH = input("Please enter your API Hash: ")


async def export_session():
    async with Client(
        "generator",
        api_id=API_ID,
        api_hash=API_HASH,
        lang_code="ar",
        device_model="MacBook Pro M1",
        system_version="14.3.1",
    ) as app:
        session_string = await app.export_session_string()
        await app.send_message("me", f"STRING_SESSION: \n`{session_string}`")


asyncio.run(export_session())
