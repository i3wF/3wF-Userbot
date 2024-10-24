from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command


@Client.on_message(command("هاه") & filters.me)
async def error_command(client: Client, message: Message):
    chat_id = message.chat.id
    await message.edit("هاه؟")
    await client.send_sticker(
        chat_id,
        sticker="CAACAgQAAxkBAAEMVGFmHKq8cX528AmoCIWy5wIB_Sb7sQACXxQAAo9c6VOlTlHwzFALUzQE",
    )
    await client.send_sticker(
        chat_id,
        sticker="CAACAgQAAxkBAAEMVGVmHKq-wim9V1v4rzjBFybrY1HMPwACUhAAAonX8VP2zYXKz6o1VjQE",
    )
    await client.send_sticker(
        chat_id,
        sticker="CAACAgQAAxkBAAEMVGNmHKq9GOF_C3_NmK0ROdaEo_8xUgACjg4AAiWp4VNPXa3cqWN_ujQE",
    )


module = modules_help.add_module("هاه", __file__)
module.add_command("هاه اذا مافهمت كلام الشخص الي يتكلم")
