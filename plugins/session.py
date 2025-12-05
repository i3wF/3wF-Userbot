from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command


@Client.on_message(command("export session") & filters.me)
async def string_session_exporter(client: Client, message: Message):
    await message.edit("check your DMs")
    await client.send_message("me", f"your session string:\n<code>{await client.export_session_string()}</code>")

module = modules_help.add_module("cmds", __file__)
module.add_command("export session", "export your session string")
