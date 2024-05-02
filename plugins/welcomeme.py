from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command

@Client.on_message(filters.new_chat_members)
async def join_3wF(client: Client, message: Message):
    for member in message.new_chat_members:
        if member.id == 6979397476:
            await message.reply_video('i3wf.MP4',caption="The general 3wF was joined the group!", quote=True)