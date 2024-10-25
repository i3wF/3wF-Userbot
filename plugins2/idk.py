from pyrogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    InlineQuery,
)
from youtube_search import YoutubeSearch
from pyrogram import Client
import threading
import asyncio
import aiohttp
import random
import string
import yt_dlp
import json
import os


FIRE_THUMB = "https://i.imgur.com/qhYYqZa.png"


def generate_random_filename(length=10):
    """Generate a random filename."""
    letters_and_digits = string.ascii_letters + string.digits
    return "".join(random.choice(letters_and_digits) for _ in range(length))


async def fetch_thumbnails(session, url):
    async with session.get(url) as response:
        return await response.read()


async def search_youtube(query):
    return YoutubeSearch(query, max_results=4).to_dict()


async def send_audio(
    client: Client, chat_id, msg_id, audio_file, rep, thumb, title, duration
):
    return await client.send_audio(
        chat_id=chat_id,
        audio=audio_file,
        caption=rep,
        thumbnail=thumb,
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


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))


user_data = {}


@Client.on_callback_query(group=610)
async def callback_query_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    if data.startswith("r_"):
        data_parts = callback_query.data.split("_")
        if len(data_parts) != 3:
            return
        _, msg_id, index = data_parts
        msg_id = int(msg_id)
        index = int(index)
        if (
            msg_id in user_data
            and "callback_data_stored" in user_data[msg_id]
            and "video_urls" in user_data[msg_id]
            and user_data[msg_id]["user_id"] == callback_query.from_user.id
        ):
            callback_data_stored = user_data[msg_id]["callback_data_stored"]
            video_urls = user_data[msg_id]["video_urls"]
        else:
            return
        search_query = [item[2] for item in callback_data_stored if item[1] == index][0]
        await client.delete_messages(
            chat_id=callback_query.message.chat.id,
            message_ids=[callback_query.message.id],
        )
        file_ids = load_file_id()
        url_suffix = video_urls[index][1]
        try:
            video_id = url_suffix.split("watch?v=")[-1].split("&")[0]
            if video_id in file_ids:
                audio_id = file_ids[video_id]
                await client.send_audio(
                    chat_id=callback_query.message.chat.id,
                    audio=audio_id,
                    caption=f"𝗖𝗵𝗮 ➤ @{client.me.username}",
                    reply_to_message_id=msg_id,
                )
                save_file_id(video_id, audio_id)
                user_data.pop(msg_id)
            else:
                downloads_dir = "downloads"
                if not os.path.exists(downloads_dir):
                    os.makedirs(downloads_dir)
                results = await search_youtube(search_query)
                link = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"][:40]
                thumbnail = results[0]["thumbnails"][0]
                async with aiohttp.ClientSession() as session:
                    thumb_data = await fetch_thumbnails(session, thumbnail)
                thumb = f"{downloads_dir}/{random.randint(1, 100000)}.jpg"
                with open(thumb, "wb") as f:
                    f.write(thumb_data)
                loop = asyncio.get_event_loop()
                thread = threading.Thread(
                    target=download_audio,
                    args=(
                        loop,
                        client,
                        callback_query.message,
                        msg_id,
                        link,
                        video_id,
                        title,
                        results[0]["duration"],
                        thumb,
                        downloads_dir,
                    ),
                )
                thread.start()
        except Exception as e:
            await callback_query.message.reply_text(
                f"حدثت مشكلة أثناء تحميل الصوت. يرجى المحاولة مرة أخرى لاحقًا. Error: {str(e)}"
            )
            print(e)
        user_data.pop(msg_id)


@Client.on_inline_query(group=2)
async def inline(_, query: InlineQuery):
    string = query.query.lower()
    if string == "commands":
        help_text = (
            "Available Commands:\n\n"
            "/start - Start the bot\n"
            "/help - Get help about commands\n"
            "/about - Get information about the bot\n"
            "/settings - Configure bot settings\n"
        )
        await query.answer(
            results=[
                InlineQueryResultArticle(
                    title="Commands Help",
                    input_message_content=InputTextMessageContent(
                        help_text,
                        disable_web_page_preview=True,
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Community", url="https://t.me/pyrogram"
                                ),
                                InlineKeyboardButton(
                                    "GitHub", url="https://github.com/pyrogram"
                                ),
                                InlineKeyboardButton(
                                    "Docs", url="https://docs.pyrogram.org"
                                ),
                            ]
                        ]
                    ),
                    thumb_url=FIRE_THUMB,
                ),
            ]
        )
    elif string == "shit":
        await query.answer(
            results=[
                InlineQueryResultArticle(
                    title="shit",
                    input_message_content=InputTextMessageContent(
                        "shit",
                        disable_web_page_preview=True,
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Community", url="https://t.me/pyrogram"
                                ),
                                InlineKeyboardButton(
                                    "GitHub", url="https://github.com/pyrogram"
                                ),
                                InlineKeyboardButton(
                                    "Docs", url="https://docs.pyrogram.org"
                                ),
                            ]
                        ]
                    ),
                    thumb_url=FIRE_THUMB,
                ),
            ]
        )
    elif string.startswith("yot "):
        search_query = string[4:].strip()
        if not search_query:
            await query.answer(
                results=[
                    InlineQueryResultArticle(
                        title="Error: No search term provided.",
                        input_message_content=InputTextMessageContent(
                            "Please provide a search term after 'yot'.",
                            disable_web_page_preview=True,
                        ),
                    )
                ]
            )
            return
        results = await search_youtube(search_query)
        if results:
            if query.id not in user_data:
                user_data[query.id] = {
                    "user_id": query.from_user.id,
                    "callback_data_stored": [],
                    "video_urls": [],
                }
            keyboard_buttons = []
            for index, result in enumerate(results):
                callback_data = f"r_{query.id}_{index}"
                keyboard_buttons.append(
                    [InlineKeyboardButton(result["title"], callback_data=callback_data)]
                )
                user_data[query.id]["callback_data_stored"].append(
                    (
                        query.from_user.id,
                        index,
                        result["title"],
                        result.get("url_suffix", ""),
                    )
                )
                user_data[query.id]["video_urls"].append(
                    (index, result.get("url_suffix", ""))
                )
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            await query.answer(
                results=[
                    InlineQueryResultArticle(
                        title=f"Results for: {search_query}",
                        input_message_content=InputTextMessageContent(
                            f"Search results for: {search_query}",
                            disable_web_page_preview=True,
                        ),
                        reply_markup=keyboard,
                        thumb_url=FIRE_THUMB,
                    ),
                ]
            )
