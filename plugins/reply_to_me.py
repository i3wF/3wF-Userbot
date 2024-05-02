from pyrogram.types import Sticker, Video, Photo, Animation, Audio, Voice
from pyrogram import Client, filters
from pyrogram.types import Message

from datetime import datetime
from dotenv import dotenv_values
import pytz

env = dotenv_values("./.env")

def get_env_value(key: str, to_type, default=None):
    value = env.get(key)
    if value is None:
        return default

    try:
        return to_type(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid value for {key}: {value}") from e
    
reply_group = get_env_value("REPLY_GROUP", str)

@Client.on_message(filters.group & filters.reply)
async def reply_to_me(client: Client, message: Message):
    CMI = client.me.id
    GID = reply_group
    link = message.link
    user_id = message.from_user.id
    riyadh_timezone = pytz.timezone('Asia/Riyadh')
    current_time = datetime.now(riyadh_timezone)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    user_info = await client.get_users(user_id)
    name = user_info.first_name if user_info.first_name else "N/A"
    mention = f"@{user_info.username}" if user_info.username else f"({name})[tg://user?id={user_id}]"
    if message.reply_to_message and message.reply_to_message.from_user.id == CMI and message.from_user.id != CMI:
        response_message = message.text or message.video or message.sticker or message.animation or message.photo or message.audio or message.voice
        if isinstance(response_message, Video):
            type = "فيديو"
            RTM = f"\nيوجد شخصاً ما رد عليك {mention}\nاسمه: {name}\nايديه: {user_id}\nرابط الرسالة : {link}\nنوع الرسالة: {type}\nالوقت: {formatted_time}"
            await client.send_message(GID, RTM)
            await client.send_video(GID, video=message.video.file_id)
        elif isinstance(response_message, Sticker):
            type = "ملصق"
            RTM = f"\nيوجد شخصاً ما رد عليك {mention}\nاسمه: {name}\nايديه: {user_id}\nرابط الرسالة : {link}\nنوع الرسالة: {type}\nالوقت: {formatted_time}"
            await client.send_message(GID, RTM)
            await client.send_sticker(GID, sticker=message.sticker.file_id)
        elif isinstance(response_message, Animation):
            type = "متحرك"
            RTM = f"\nيوجد شخصاً ما رد عليك {mention}\nاسمه: {name}\nايديه: {user_id}\nرابط الرسالة : {link}\nنوع الرسالة: {type}\nالوقت: {formatted_time}"
            await client.send_message(GID, RTM)
            await client.send_animation(GID, animation=message.animation.file_id)
        elif isinstance(response_message, Photo):
            type = "صورة"
            RTM = f"\nيوجد شخصاً ما رد عليك {mention}\nاسمه: {name}\nايديه: {user_id}\nرابط الرسالة : {link}\nنوع الرسالة: {type}\nالوقت: {formatted_time}"
            await client.send_message(GID, RTM)
            await client.send_photo(GID, photo= message.photo.file_id)
        elif isinstance(response_message, Audio):
            type = "صوتي"
            RTM = f"\nيوجد شخصاً ما رد عليك {mention}\nاسمه: {name}\nايديه: {user_id}\nرابط الرسالة : {link}\nنوع الرسالة: {type}\nالوقت: {formatted_time}"
            await client.send_message(GID, RTM)
            await client.send_audio(GID, audio= message.audio.file_id)
        elif isinstance(response_message, Voice):
            type = "فويس"
            RTM = f"\nيوجد شخصاً ما رد عليك {mention}\nاسمه: {name}\nايديه: {user_id}\nرابط الرسالة : {link}\nنوع الرسالة: {type}\nالوقت: {formatted_time}"
            await client.send_message(GID, RTM)
            await client.send_voice(GID, voice=message.voice.file_id)
        elif message.text:
            type = "نص"
            RTM = f"يوجد شخصاً ما رد عليك {mention}\nاسمه: {name}\nايديه: {user_id}\nرابط الرسالة : {link}\nنوع الرسالة: {type}\nمحتوى الرسالة {message.text}\nالوقت: {formatted_time}"
            await client.send_message(GID, RTM)