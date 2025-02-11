from pyrogram.types import Sticker, Video, Photo, Animation, Audio, Voice
from pyrogram import Client, filters
from pyrogram.types import Message

from dotenv import dotenv_values
from datetime import datetime
import pytz

from moviepy.editor import VideoFileClip
import string, random
from PIL import Image
import io, os
import asyncio


def generate_random_filename(length=10):
    """Generate a random filename."""
    letters_and_digits = string.ascii_letters + string.digits
    return "".join(random.choice(letters_and_digits) for _ in range(length))


async def media_to_sticker(input_media, output_media):
    cmd = [
        "ffmpeg",
        "-nostdin",
        "-y",
        "-i",
        input_media,
        "-t",
        "3",
        "-an",
        "-crf",
        "36",
        "-r",
        "30",
        "-c:v",
        "libvpx-vp9",
        output_media,
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await process.communicate()
    return output_media


def get_env_value(key: str, to_type, default=None):
    value = env.get(key)
    if value is None:
        return default
    try:
        return to_type(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid value for {key}: {value}") from e


env = dotenv_values("./.env")
GID = get_env_value("REPLIES_ID", str)


@Client.on_message(filters.group & filters.reply & ~filters.me & ~filters.bot)
async def reply_to_me(client: Client, message: Message):
    link = message.link
    user_id = message.from_user.id if message.from_user.id else message.sender_chat.id
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
    replied_msg_id = message.reply_to_message.from_user.id
    if replied_msg_id == client.me.id:
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
                f"\nيوجد شخصٌ ما رد عليك {mention}\n"
                f"الاسم: {name}\n"
                f"الايدي: {user_id}\n"
                f"رابط الرسالة : {link}\n"
                f"نوع الرسالة: {type_label}\n"
                f"الوقت: {formatted_time}"
            )

            if message_type is str and text:
                RTM += f"\nمحتوى الرسالة: {text}"

            await client.send_message(chat_id=GID, text=RTM)

            if message_type is Sticker:
                file_path = await client.download_media(file_id)

                if response_message.is_video or response_message.is_animated:
                    video_name = f"{generate_random_filename()}.mp4"
                    clip = VideoFileClip(file_path)
                    clip.write_videofile(video_name)
                    await client.send_video(chat_id=GID, video=video_name)
                    os.remove(video_name)

                else:
                    with Image.open(file_path) as img:
                        img = img.convert("RGBA")
                        png_bytes = io.BytesIO()
                        img.save(png_bytes, format="PNG")
                        png_bytes.seek(0)
                        await client.send_photo(chat_id=GID, photo=png_bytes)

                os.remove(file_path)
            else:
                if file_id:
                    await {
                        Video: client.send_video,
                        Animation: client.send_animation,
                        Photo: client.send_photo,
                        Audio: client.send_audio,
                        Voice: client.send_voice,
                    }[message_type](
                        chat_id=GID, **{message_type.__name__.lower(): file_id}
                    )

        if isinstance(
            response_message, (Video, Sticker, Animation, Photo, Audio, Voice)
        ):
            await send_response(type(response_message), response_message.file_id)

        elif message.text:
            await send_response(str, text=message.text)
