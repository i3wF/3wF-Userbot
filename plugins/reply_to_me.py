from pyrogram.types import Sticker, Video, Photo, Animation, Audio, Voice
from pyrogram import Client, filters
from pyrogram.types import Message

from datetime import datetime
import pytz
import os

GID = os.getenv("REPLIES_ID")


@Client.on_message(filters.group & filters.reply & ~filters.me & ~filters.bot)
async def reply_to_me(client: Client, message: Message):
    link = message.link
    user_id = message.from_user.id
    riyadh_timezone = pytz.timezone("Asia/Riyadh")
    current_time = datetime.now(riyadh_timezone)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    user_info = await client.get_users(user_id)
    name = user_info.first_name if user_info.first_name else "N/A"
    mention = (
        f"@{user_info.username}"
        if user_info.username
        else f"({name})[tg://user?id={user_id}]"
    )

    if message.reply_to_message.from_user.id == client.me.id:
        response_message = (
            message.text
            or message.video
            or message.sticker
            or message.animation
            or message.photo
            or message.audio
            or message.voice
        )

        async def send_response(message_type, file_id=None, text=None):
            type_translations = {
                Video: "فيديو",
                Sticker: "ملصق",
                Animation: "متحرك",
                Photo: "صورة",
                Audio: "صوتي",
                Voice: "فويس",
                str: "نص",
            }

            type_label = type_translations.get(message_type, "نص")

            RTM = (
                f"\nيوجد شخصاً ما رد عليك {mention}\n"
                f"اسمه: {name}\n"
                f"ايديه: {user_id}\n"
                f"رابط الرسالة : {link}\n"
                f"نوع الرسالة: {type_label}\n"
                f"الوقت: {formatted_time}"
            )

            if message_type is str and text:
                RTM += f"\nمحتوى الرسالة: {text}"

            await client.send_message(chat_id=GID, text=RTM)

            if file_id:
                await {
                    Video: client.send_video,
                    Sticker: client.send_sticker,
                    Animation: client.send_animation,
                    Photo: client.send_photo,
                    Audio: client.send_audio,
                    Voice: client.send_voice,
                }[message_type](chat_id=GID, **{message_type.__name__.lower(): file_id})

        if isinstance(
            response_message, (Video, Sticker, Animation, Photo, Audio, Voice)
        ):
            await send_response(type(response_message), response_message.file_id)

        elif message.text:
            await send_response(str, text=message.text)
