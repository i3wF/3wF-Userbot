from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command 


@Client.on_message(command("cmds") & filters.me)
async def cmds(client: Client, message: Message):
    x = await client.get_inline_bot_results("Hayday3wFbot", "")
    for y in x.results:
        await client.send_inline_bot_result(message.chat.id, x.query_id, y.id, reply_to_message_id=message.id)


module = modules_help.add_module("cmds", __file__)
module.add_command("cmds", "لرؤية الاوامر الخاصة باليوزربوت")