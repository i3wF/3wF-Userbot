from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.regex(r"^تاقي$") & filters.me)
async def tagi(client: Client, message: Message):
    await message.edit(
        "أساسية - الشخصية\n#LC22YYQ80\n\nثانوية - شخصية\n#LY28PL8GC\n\n--(تاق الاسطورة)--"
    )
