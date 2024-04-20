from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command

from datetime import datetime
import pytz

@Client.on_message(filters.command("عوف","") & filters.group)
async def get_3wF(client: Client, message: Message):
    user_id = message.from_user.id
    user_info = await client.get_users(user_id)
    name = user_info.first_name if user_info.first_name else "N/A"
    mention = f"@{user_info.username}" if user_info.username else f"({name})[t.me/user?id={user_id}]"
    riyadh_timezone = pytz.timezone('Asia/Riyadh')
    current_time = datetime.now(riyadh_timezone)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    link = message.link
    await client.send_message(chat_id=message.chat.id, text=f"• The power of Thought • \n\n • don't spam please •", reply_to_message_id=message.id)
    await client.send_message(chat_id='-4158625241', text=f"""شخصاُ ما يناديك {mention}\nاسمه: {name}\nايديه: {user_id}\nرابط الرسالة: {link}\n\nالوقت: {formatted_time}""")