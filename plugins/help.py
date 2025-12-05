from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command
from utils.db import db


@Client.on_message(command(["cmds", "shit"]) & filters.me)
async def cmds(client: Client, message: Message):
    if message.command[0] == "cmds":
        text = "commands"
    elif message.command[0] == "shit":
        text = "shit"
    try:
        x = await client.get_inline_bot_results(db.get("core", "bot_username"), text)
        for m in x.results:
            await client.send_inline_bot_result(
                message.chat.id, x.query_id, m.id, reply_to_message_id=message.id
            )
    except Exception as error:
        await message.edit(str(error))


module = modules_help.add_module("cmds", __file__)
module.add_command("cmds", "لرؤية الاوامر الخاصة باليوزربوت")
