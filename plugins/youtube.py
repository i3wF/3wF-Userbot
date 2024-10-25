from youtube_search import YoutubeSearch
from pyrogram import Client, filters
from pyrogram.types import Message
import threading
import requests
import asyncio
import random
import string
import yt_dlp
import json
import os


def generate_random_filename(length=10):
    """Generate a random filename."""
    letters_and_digits = string.ascii_letters + string.digits
    return "".join(random.choice(letters_and_digits) for _ in range(length))


async def search_youtube(query):
    return YoutubeSearch(query, max_results=4).to_dict()


async def send_audio(
    client: Client, chat_id, msg_id, audio_file, rep, thumb, title, duration
):
    return await client.send_audio(
        chat_id=chat_id,
        audio=audio_file,
        caption=rep,
        thumb=thumb,
        title=title,
        duration=duration,
        reply_to_message_id=msg_id,
    )


async def send_message(client: Client, chat_id, msg_id, text):
    return await client.send_message(
        chat_id=chat_id,
        text=text,
        reply_to_message_id=msg_id,
    )


def download_audio(
    loop, client, message, msg_id, link, video_id, title, duration, thumb, downloads_dir
):
    try:
        ydl_opts = {
            "format": "bestaudio[ext=m4a]",
            "outtmpl": f"{downloads_dir}/{generate_random_filename()}.%(ext)s",
            "username": "oauth2",
            "password": "",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            audio_file = ydl.prepare_filename(info_dict)
            base, ext = os.path.splitext(audio_file)
            new_file = base + ".m4a"
            os.rename(audio_file, new_file)
        rep = f"𝗖𝗵𝗮 ➤ @{client.me.username}"
        secmul, dur, dur_arr = 1, 0, duration.split(":")
        for i in range(len(dur_arr) - 1, -1, -1):
            dur += int(dur_arr[i]) * secmul
            secmul *= 60
        sent_message_future = asyncio.run_coroutine_threadsafe(
            send_audio(
                client, message.chat.id, msg_id, new_file, rep, thumb, title, dur
            ),
            loop,
        )
        sent_message = sent_message_future.result()
        save_file_id(video_id, sent_message.audio.file_id)
        os.remove(new_file)
        os.remove(thumb)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(
            send_message(
                client,
                message.chat.id,
                msg_id,
                "حدثت مشكلة أثناء تحميل الصوت. يرجى المحاولة مرة أخرى لاحقًا.",
            ),
            loop,
        )
        print(e)


def load_file_id():
    os.makedirs("Database", exist_ok=True)
    try:
        with open(f"Database/file_ids.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return


def save_file_id(query, file_id):
    file_ids = load_file_id()
    file_ids[query] = file_id
    os.makedirs("Database", exist_ok=True)
    with open(f"Database/file_ids.json", "w") as f:
        json.dump(file_ids, f, indent=2)


@Client.on_message(filters.regex(r"^بحث") & filters.me)
async def search_command(client: Client, message: Message):
    search_query = (
        message.text.split(" ", 1)[1] if len(message.text.split(" ")) > 1 else ""
    )
    if not search_query:
        await message.reply_text("يرجى تقديم عبارة بحث بعد الأمر 'بحث'.")
        return
    try:
        x = await client.get_inline_bot_results("Hayday3wFbot", f"yot {search_query}")
        for m in x.results:
            await client.send_inline_bot_result(
                message.chat.id, x.query_id, m.id, reply_to_message_id=message.id
            )
    except Exception as error:
        await message.reply_text(str(error))


@Client.on_message(filters.regex(r"^يوت") & filters.me)
async def yot(client: Client, message: Message):
    query = message.text.split(" ", 1)[1] if len(message.text.split(" ")) > 1 else ""
    downloads_dir = "downloads"
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)
    file_ids = load_file_id()
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        if results:
            video_id = results[0]["id"]
            link = f"https://youtube.com{results[0]['url_suffix']}"
            title = results[0]["title"][:40]
            thumbnail = results[0]["thumbnails"][0]
            thumb = f"{downloads_dir}/{random.randint(1, 100000)}.jpg"
            thumb1 = requests.get(thumbnail, allow_redirects=True)
            open(thumb, "wb").write(thumb1.content)
            duration = results[0]["duration"]
            if video_id in file_ids:
                audio_id = file_ids[video_id]
                await message.reply_audio(
                    audio_id,
                    caption=f"𝗖𝗵𝗮 ➤ @{client.me.username}",
                )
                return
            loop = asyncio.get_event_loop()
            thread = threading.Thread(
                target=download_audio,
                args=(
                    loop,
                    client,
                    message,
                    message.id,
                    link,
                    video_id,
                    title,
                    duration,
                    thumb,
                    downloads_dir,
                ),
            )
            thread.start()
    except Exception as e:
        await message.reply_text(
            "حدثت مشكلة أثناء تحميل الصوت. يرجى المحاولة مرة أخرى لاحقًا."
        )
        print(e)
