from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.regex(r"^هاه$") & filters.me)
async def error_command(client: Client, message: Message):
    await client.send_sticker(
        chat_id=message.chat.id,
        sticker="CAACAgQAAxkBAAEMVGFmHKq8cX528AmoCIWy5wIB_Sb7sQACXxQAAo9c6VOlTlHwzFALUzQE",
        reply_to_message_id=message.reply_to_message.id,
    )
    await client.send_sticker(
        chat_id=message.chat.id,
        sticker="CAACAgQAAxkBAAEMVGVmHKq-wim9V1v4rzjBFybrY1HMPwACUhAAAonX8VP2zYXKz6o1VjQE",
        reply_to_message_id=message.reply_to_message.id,
    )
    await client.send_sticker(
        chat_id=message.chat.id,
        sticker="CAACAgQAAxkBAAEMVGNmHKq9GOF_C3_NmK0ROdaEo_8xUgACjg4AAiWp4VNPXa3cqWN_ujQE",
        reply_to_message_id=message.reply_to_message.id,
    )
