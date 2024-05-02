from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command

@Client.on_message(filters.command("السلام عليكم","") & filters.private)
async def example_send(client: Client, message: Message):
    await message.reply_text("وعليكم السلام", quote=True)