from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.regex(r"^بنام$") & filters.me)
async def going_sleep(client: Client, message: Message):
    chat_id = message.chat.id
    await message.edit("بنام تصبحون على ما تمسون")
    await client.send_sticker(
        chat_id,
        sticker="CAACAgQAAxkBAAEMVHdmHRNU0CsciVvuGqU1DCA7ePo1uQACHg0AAuS4cFLGSCyrVskf8TQE",
    )


@Client.on_message(filters.regex(r"^نوم$") & filters.me)
async def sleep(client: Client, message: Message):
    chat_id = message.chat.id
    await message.edit(
        "نوم العوافي",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(client.me.first_name, user_id="6979397476")]]
        ),
    )
    await client.send_sticker(
        chat_id,
        sticker="CAACAgQAAxkBAAEMVF9mHKjg6HxqOQtNd0QH-fZJBat2jQACbA8AAtyByVCW2JiDS51lvDQE",
    )


@Client.on_message(filters.regex(r"^نام$") & filters.me)
async def goto_sleep(client: Client, message: Message):
    chat_id = message.chat.id
    await message.edit("نام بالله")
    await client.send_sticker(
        chat_id,
        sticker="CAACAgQAAxkBAAEMVHxmHRZigUv2HvqZ5_B_zoXocacc8wACfwwAAj2C2FE4TVuFzWYh1zQE",
    )


@Client.on_message(filters.regex(r"^نامي$") & filters.me)
async def goto_sleep2(client: Client, message: Message):
    chat_id = message.chat.id
    await message.edit("نامي بالله")
    await client.send_sticker(
        chat_id,
        sticker="CAACAgIAAxkBAAEMVFtmHKeFuyoqdeMF-fH_Pe_lodCp8gAC5zYAAlznmUh05CgmiJEEIzQE",
    )
