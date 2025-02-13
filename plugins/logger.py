from pyrogram import Client, filters
from pyrogram.types import Message
from utils.db import RedisHandler

import pytz

redis_handler = RedisHandler()


async def get_message_type_and_file_id(msg: Message):
    if msg.photo:
        return "photo", msg.photo.file_id, msg.caption
    elif msg.document:
        return "document", msg.document.file_id, msg.caption
    elif msg.video:
        return "video", msg.video.file_id, msg.caption
    elif msg.audio:
        return "audio", msg.audio.file_id, msg.caption
    elif msg.voice:
        return "voice", msg.voice.file_id, None
    elif msg.sticker:
        return "sticker", msg.sticker.file_id, None
    elif msg.animation:
        return "animation", msg.animation.file_id, msg.caption
    elif msg.location:
        return "location", f"{msg.location.latitude},{msg.location.longitude}", None
    elif msg.contact:
        return "contact", f"{msg.contact.phone_number}", None
    elif msg.text:
        return "text", None, msg.text


async def save_message_to_redis(message: Message, message_type, file_id, caption):
    riyadh_tz = pytz.timezone("Asia/Riyadh")
    date_riyadh = message.date.astimezone(riyadh_tz)
    date_str = date_riyadh.strftime("%Y-%m-%d %H:%M:%S")
    message_data = {
        "message_id": message.id,
        "text": message.text if message.text else "",
        "caption": "" if message.text else caption,
        "message_type": message_type,
        "file_id": file_id if file_id else "",
        "date": date_str,
    }
    redis_key = f"{message.chat.type}:{message.from_user.id}:{message.id}"
    redis_handler.hset(redis_key, mapping=message_data)
    print(f"تم تسجيل الرسالة في Redis: {redis_key}")


async def save_sender_data_to_redis(user):
    sender_data = {
        "user_id": user.id,
        "username": user.username or "none",
        "first_name": user.first_name or "none",
        "last_name": user.last_name or "none",
    }
    user_key = f"user:{user.id}"

    data_to_save = {}
    if sender_data["username"] != "none":
        data_to_save["username"] = sender_data["username"]
    if sender_data["first_name"] != "none":
        data_to_save["first_name"] = sender_data["first_name"]
    if sender_data["last_name"] != "none":
        data_to_save["last_name"] = sender_data["last_name"]

    if data_to_save:
        redis_handler.hset(user_key, mapping=data_to_save)

    if sender_data["username"] != "none" and sender_data[
        "username"
    ] not in redis_handler.lrange(f"{user_key}:usernames", 0, -1):
        redis_handler.lpush(f"{user_key}:usernames", sender_data["username"])

    if sender_data["first_name"] != "none" and sender_data[
        "first_name"
    ] not in redis_handler.lrange(f"{user_key}:first_names", 0, -1):
        redis_handler.lpush(f"{user_key}:first_names", sender_data["first_name"])

    if sender_data["last_name"] != "none" and sender_data[
        "last_name"
    ] not in redis_handler.lrange(f"{user_key}:last_names", 0, -1):
        redis_handler.lpush(f"{user_key}:last_names", sender_data["last_name"])


@Client.on_message(filters.private & ~filters.me & ~filters.bot, group=1236)
async def handle_private_message(client: Client, message: Message):
    message_type, file_id, caption = await get_message_type_and_file_id(message)
    if message.from_user:
        await save_sender_data_to_redis(message.from_user)

    await save_message_to_redis(message, message_type, file_id, caption)


@Client.on_message(
    filters.group & filters.reply & ~filters.me & ~filters.bot, group=1237
)
async def handle_group_reply(client: Client, message: Message):
    replied_msg_id = (
        message.reply_to_message.from_user.id
        if message.reply_to_message.from_user.id
        else message.reply_to_message.sender_chat.id
        if message.reply_to_message.sender_chat
        else None
    )
    if replied_msg_id == client.me.id:
        message_type, file_id, caption = await get_message_type_and_file_id(message)
        if message.from_user:
            await save_sender_data_to_redis(message.from_user)

        await save_message_to_redis(message, message_type, file_id, caption)


@Client.on_message(filters.regex(r"^كشف") & filters.me, group=1238)
async def check_command(client: Client, message: Message):
    user_query = (
        message.text.split(" ", 1)[1] if len(message.text.split(" ")) > 1 else ""
    )
    if not user_query:
        await message.reply_text(
            "⚠️ الرجاء إدخال معرف المستخدم بعد الأمر. مثال: `كشف 12345678`"
        )
        return
    try:
        x = await client.get_inline_bot_results("manga3wFbot", f"check {user_query}")
        for m in x.results:
            await client.send_inline_bot_result(
                message.chat.id, x.query_id, m.id, reply_to_message_id=message.id
            )
    except Exception as error:
        await message.reply_text(str(error))
