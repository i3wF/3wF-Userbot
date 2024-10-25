from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command


@Client.on_message(
    filters.regex(r"السلام عليكم|السلام|السلام عليكم ورحمة الله وبركاته|سلام عليكم|")
    & filters.private
    & ~filters.me
)
async def welcomer(client: Client, message: Message):
    await message.reply_text("وعليكم السلام\nامرني وتدلل", quote=True)
