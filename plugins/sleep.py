from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command

@Client.on_message(command("بنام") & filters.me)
async def example_send(client: Client, message: Message):
    chat_id = message.chat.id
    await message.edit("بنام تصبحون على ما تمسون")
    await client.send_sticker(chat_id, sticker="CAACAgQAAxkBAAEMVHdmHRNU0CsciVvuGqU1DCA7ePo1uQACHg0AAuS4cFLGSCyrVskf8TQE")

@Client.on_message(command("نوم") & filters.me)
async def example_send(client: Client, message: Message):
    chat_id = message.chat.id
    await message.edit("نوم العوافي", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(client.me.first_name, user_id="6979397476")]]))
    await client.send_sticker(chat_id, sticker="CAACAgQAAxkBAAEMVF9mHKjg6HxqOQtNd0QH-fZJBat2jQACbA8AAtyByVCW2JiDS51lvDQE")
    

@Client.on_message(command("نام") & filters.me)
async def example_send(client: Client, message: Message):
    chat_id = message.chat.id
    await message.edit("نام بالله")
    await client.send_sticker(chat_id, sticker="CAACAgQAAxkBAAEMVHxmHRZigUv2HvqZ5_B_zoXocacc8wACfwwAAj2C2FE4TVuFzWYh1zQE")

@Client.on_message(command("نامي") & filters.me)
async def example_send(client: Client, message: Message):
    chat_id = message.chat.id
    await message.edit("نامي بالله")
    await client.send_sticker(chat_id, sticker="CAACAgIAAxkBAAEMVFtmHKeFuyoqdeMF-fH_Pe_lodCp8gAC5zYAAlznmUh05CgmiJEEIzQE")

module = modules_help.add_module("النوم", __file__)
module.add_command("نامي", "لتنويم البنات اكتب هيك")
module.add_command("نام", "لتنويم العيال اكتب هيك")
module.add_command("نوم", "لتمني بالنومة الهنيئة")
module.add_command("بنام", "لتنويم نفسك")