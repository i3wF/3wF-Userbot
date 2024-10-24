from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command


@Client.on_message(command("تاقي") & filters.me)
async def tagi(client: Client, message: Message):
    await message.edit(
        "أساسية - الشخصية\n#LC22YYQ80\n\nثانوية - شخصية\n#LY28PL8GC\n\n--(تاق الاسطورة)--"
    )


module = modules_help.add_module("تاقي", __file__)
module.add_command("تاقي [لاظهار تاقك في هاي داي]")
