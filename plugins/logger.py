from pyrogram import Client, filters
from pyrogram.types import Message
from utils.db import RedisHandler

import time


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


async def save_message_to_redis(
    message: Message, message_type, file_id, caption, current_time
):
    message_data = {
        "text": message.text if message.text else "",
        "caption": caption if caption else "",
        "message_type": message_type,
        "file_id": file_id if file_id else "",
        "date": current_time,
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
    redis_handler.hset(user_key, mapping=sender_data)
    redis_handler.lpush(f"{user_key}:usernames", sender_data["username"])
    redis_handler.lpush(f"{user_key}:first_names", sender_data["first_name"])
    redis_handler.lpush(f"{user_key}:last_names", sender_data["last_name"])


@Client.on_message(filters.private & ~filters.me & ~filters.bot, group=1236)
async def handle_private_message(client: Client, message: Message):
    current_time = time.time()
    message_type, file_id, caption = await get_message_type_and_file_id(message)
    if message.from_user:
        await save_sender_data_to_redis(message.from_user)

    await save_message_to_redis(message, message_type, file_id, caption, current_time)


@Client.on_message(
    filters.group & filters.reply & ~filters.me & ~filters.bot, group=1237
)
async def handle_group_reply(client: Client, message: Message):
    if (
        message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == client.me.id
    ):
        current_time = time.time()
        message_type, file_id, caption = await get_message_type_and_file_id(message)
        if message.from_user:
            await save_sender_data_to_redis(message.from_user)

        await save_message_to_redis(
            message, message_type, file_id, caption, current_time
        )
