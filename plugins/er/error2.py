from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command


@Client.on_message(command("علقت") & filters.me)
async def error_command(client: Client, message: Message):
    chat_id = message.chat.id
    if message.reply_to_message:
        await message.delete()
        await client.send_sticker(
            chat_id,
            sticker="CAACAgIAAxkBAAEMVH5mHRcyXlLOmrLnBisEBYDIu1F3wgACtCMAAphLKUjeub7NKlvk2TQE",
            reply_to_message_id=message.reply_to_message.id,
        )
    else:
        await message.edit("Usage: by reply to messages")


module = modules_help.add_module("علقت", __file__)
module.add_command("علقت [اذا علق مخك ومافهمت وش يقول الشخص]")
