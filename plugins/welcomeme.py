from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.new_chat_members)
async def join_3wF(client: Client, message: Message):
    for member in message.new_chat_members:
        if member.id == client.me.id:
            await message.reply_video(
                "i3wf.MP4", caption="The general 3wF was joined the group!", quote=True
            )
