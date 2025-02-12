from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from pyrogram.enums import ChatType, ParseMode
from pyrogram import Client, filters
from convopyro import listen_message
from utils.db import RedisHandler
from dotenv import load_dotenv
from datetime import datetime
from main import app

import asyncio
import pytz
import os

load_dotenv()

redis_handler = RedisHandler()


async def format_date(timestamp):
    try:
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
        riyadh_timezone = pytz.timezone("Asia/Riyadh")
        datetime_obj = datetime.fromtimestamp(timestamp, riyadh_timezone)
        formatted_time = datetime_obj.strftime("%Y-%m-%d %I:%M %p")
        return formatted_time
    except ValueError:
        return "التاريخ غير متاح"


async def fetch_messages(user_id, message_type, search_term=None, page=1):
    if message_type == "group":
        keys = redis_handler.keys(f"{ChatType.GROUP}:{user_id}:*") + redis_handler.keys(
            f"{ChatType.SUPERGROUP}:{user_id}:*"
        )
    else:
        keys = redis_handler.keys(f"{message_type}:{user_id}:*")
    if not keys:
        return "🚫 لا توجد رسائل لهذا المستخدم.", None

    if search_term:
        keys = [
            key
            for key in keys
            if search_term.lower() in redis_handler.hget(key, "text").lower()
        ]

    if not keys:
        return f"🚫 لا توجد رسائل تحتوي على الكلمة '{search_term}'.", None

    reply_markup = None
    total_messages = len(keys)
    messages_per_page = 3
    start_index = (page - 1) * messages_per_page
    end_index = start_index + messages_per_page
    keys_to_display = keys[start_index:end_index]
    if message_type == ChatType.GROUP or ChatType.SUPERGROUP:
        message_type_ar = "القروب"
    else:
        message_type_ar = "الخاص"
    result = f"📊 نتائج الاستعلام في- {message_type_ar}:\n"
    result += f"📥 إجمالي الرسائل: {total_messages}\n\n"

    for key in keys_to_display:
        message_data = redis_handler.hgetall(key)
        msg_type = message_data.get("message_type")
        msg_type_map = {
            "text": "نص",
            "contact": "جهة اتصال",
            "location": "موقع",
            "animation": "صورة متحركة",
            "sticker": "ملصق",
            "voice": "رسالة صوتية",
            "audio": "صوت",
            "video": "فيديو",
            "document": "ملف",
            "photo": "صورة",
        }
        formatted_msg_type = msg_type_map.get(msg_type, "غير معروف")
        if msg_type == "text":
            message_info = (
                f"📅 التاريخ: {await format_date(message_data.get('date'))}\n"
                f"✉️ نوع الرسالة: {formatted_msg_type}\n"
                f"📝 النص: {message_data.get('text')}\n"
            )
        elif msg_type in ["photo", "video", "animation", "audio", "document"]:
            message_info = (
                f"📅 التاريخ: {await format_date(message_data.get('date'))}\n"
                f"✉️ نوع الرسالة: {formatted_msg_type}\n"
                f"📎 الكابشن: {message_data.get('caption')}\n"
            )
        else:
            message_info = (
                f"📅 التاريخ: {await format_date(message_data.get('date'))}\n"
                f"✉️ نوع الرسالة: {formatted_msg_type}\n"
                f"📝 النص: {message_data.get('text')}\n"
            )
        file_id = message_data.get("file_id")
        if file_id != "none" and file_id:
            download_button = InlineKeyboardButton(
                "🔗 تحميل الميديا",
                callback_data=f"dm_{message_type}_{user_id}_{message_data.get('message_id')}",
            )
            reply_markup = InlineKeyboardMarkup([[download_button]])

        result += message_info
        result += "\n--------------------------\n"

    total_pages = len(keys) // messages_per_page + (
        1 if len(keys) % messages_per_page > 0 else 0
    )

    if total_pages > 1:
        buttons = []
        if page > 1:
            buttons.append(
                InlineKeyboardButton(
                    "◀️ السابق",
                    callback_data=f"page:{user_id}:{message_type}:{search_term if search_term else 'none'}:{page - 1}",
                )
            )
        if page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    "التالي ▶️",
                    callback_data=f"page:{user_id}:{message_type}:{search_term if search_term else 'none'}:{page + 1}",
                )
            )

        reply_markup = InlineKeyboardMarkup([buttons])
        result += f"\n📜 صفحة {page}/{total_pages}"

    return result, reply_markup


async def fetch_messages_for_all_types(user_id, search_term, page=1):
    message_types = [ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP]
    result = ""
    keys_to_display = []
    if message_type == ChatType.GROUP or ChatType.SUPERGROUP:
        message_type_ar = "القروب"
    else:
        message_type_ar = "الخاص"

    for message_type in message_types:
        keys = redis_handler.keys(f"{message_type}:{user_id}:*")
        if not keys:
            result += f"🚫 لا توجد رسائل من نوع {message_type_ar} لهذا المستخدم.\n"
            continue

        if search_term:
            keys = [
                key
                for key in keys
                if search_term.lower() in redis_handler.hget(key, "text").lower()
            ]

        if not keys:
            result += f"🚫 لا توجد رسائل تحتوي على الكلمة '{search_term}' من نوع {message_type_ar}.\n"
            continue

        total_messages = len(keys)
        messages_per_page = 3
        start_index = (page - 1) * messages_per_page
        end_index = start_index + messages_per_page
        keys_to_display.extend(keys[start_index:end_index])

        result += f"📊 نتائج الاستعلام في- {message_type_ar}:\n"
        result += f"📥 إجمالي الرسائل: {total_messages}\n\n"

    if not keys_to_display:
        return "🚫 لا توجد رسائل لهذا المستخدم بنوع الرسالة المحدد."

    reply_markup = None

    for key in keys_to_display:
        message_data = redis_handler.hgetall(key)
        msg_type = message_data.get("message_type")
        msg_type_map = {
            "text": "نص",
            "contact": "جهة اتصال",
            "location": "موقع",
            "animation": "صورة متحركة",
            "sticker": "ملصق",
            "voice": "رسالة صوتية",
            "audio": "صوت",
            "video": "فيديو",
            "document": "ملف",
            "photo": "صورة",
        }
        formatted_msg_type = msg_type_map.get(msg_type, "غير معروف")

        if msg_type == "text":
            message_info = (
                f"📅 التاريخ: {await format_date(message_data.get('date'))}\n"
                f"✉️ نوع الرسالة: {formatted_msg_type}\n"
                f"📝 النص: {message_data.get('text')}\n"
            )
        elif msg_type in ["photo", "video", "animation", "audio", "document"]:
            message_info = (
                f"📅 التاريخ: {await format_date(message_data.get('date'))}\n"
                f"✉️ نوع الرسالة: {formatted_msg_type}\n"
                f"📎 الكابشن: {message_data.get('caption')}\n"
            )
        else:
            message_info = (
                f"📅 التاريخ: {await format_date(message_data.get('date'))}\n"
                f"✉️ نوع الرسالة: {formatted_msg_type}\n"
                f"📝 النص: {message_data.get('text')}\n"
            )
        file_id = message_data.get("file_id")
        if file_id != "none" and file_id:
            download_button = InlineKeyboardButton(
                "🔗 تحميل الميديا",
                callback_data=f"dm_{message_types}_{user_id}_{message_data.get('message_id')}",
            )
            reply_markup = InlineKeyboardMarkup([[download_button]])

        result += message_info
        result += "\n--------------------------\n"

    total_pages = len(keys_to_display) // messages_per_page + (
        1 if len(keys_to_display) % messages_per_page > 0 else 0
    )

    if total_pages > 1:
        buttons = []
        if page > 1:
            buttons.append(
                InlineKeyboardButton(
                    "◀️ السابق",
                    callback_data=f"page:{user_id}:all:{search_term}:{page - 1}",
                )
            )
        if page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    "التالي ▶️",
                    callback_data=f"page:{user_id}:all:{search_term}:{page + 1}",
                )
            )

        reply_markup = InlineKeyboardMarkup([buttons])
        result += f"\n📜 صفحة {page}/{total_pages}"

    return result, reply_markup


@Client.on_message(
    filters.command("check") & filters.user(int(os.getenv("USER_ID"))), group=13
)
async def check_user_messages(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply(
            "⚠️ الرجاء إدخال معرف المستخدم بعد الأمر. مثال: `/check 12345678`"
        )
        return
    user_id = message.command[1]
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📩 رسائل الخاص", callback_data=f"private:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "💬 ردود المجموعات", callback_data=f"group:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔍 البحث عن كلمة", callback_data=f"search:{user_id}"
                )
            ],
        ]
    )

    await message.reply("🔍 اختر نوع الاستعلام أو البحث:", reply_markup=reply_markup)


@Client.on_callback_query(group=1313)
async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split(":")
    if data[0] == "page":
        user_id, message_type, search_term, page = (
            data[1],
            data[2],
            data[3],
            int(data[4]),
        )
        result, reply_markup = await fetch_messages(
            user_id, message_type, search_term if search_term != "none" else None, page
        )
        await callback_query.message.edit_text(
            result, reply_markup=reply_markup, parse_mode=ParseMode.DISABLED
        )

    elif data[0] in ["private", "group"]:
        message_type = data[0]
        message_type = ChatType.PRIVATE if message_type == "private" else message_type
        user_id = data[1]
        result, reply_markup = await fetch_messages(user_id, message_type)
        await callback_query.message.edit_text(
            result, reply_markup=reply_markup, parse_mode=ParseMode.DISABLED
        )

    elif data[0] == "search":
        user_id = data[1]
        await callback_query.message.edit_text("🔍 **أرسل لي الكلمة التي تبحث عنها:**")
        try:
            answer = await listen_message(
                client, callback_query.message.chat.id, timeout=60
            )
            search_term = answer.text
            result, reply_markup = await fetch_messages_for_all_types(
                user_id, search_term
            )
            await answer.reply(
                result, reply_markup=reply_markup, parse_mode=ParseMode.DISABLED
            )
        except asyncio.TimeoutError:
            await callback_query.message.edit_text(
                "⏱ **انتهى الوقت المحدد للبحث (60 ثانية).**"
            )


@Client.on_callback_query(filters.regex(r"^dm_(\d+)_(\d+)_(\d+)$"))
async def on_callback_query(client: Client, callback_query: CallbackQuery):
    message_type, user_id, message_id = callback_query.data.split("_")[1:]
    key = f"{message_type}:{user_id}:{message_id}"
    message_data = redis_handler.hgetall(key)

    if not message_data:
        await callback_query.answer("❌ الرسالة غير موجودة.")
        return

    file_id = message_data.get("file_id")

    if file_id == "none" or not file_id:
        await callback_query.answer("❌ لا يوجد ميديا لتنزيله.")
        return
    try:
        await callback_query.answer("جاري تحميل الميديا...")
        file_path = await app.download_media(file_id)
        await client.send_document(callback_query.message.chat.id, file_path)
        await callback_query.message.reply(
            f"📥 تم تحميل الميديا بنجاح.\n\n📂 المسار: {file_path}",
            parse_mode=ParseMode.MARKDOWN,
        )
        os.remove(file_path)
    except Exception as e:
        await callback_query.answer(f"❌ حدث خطأ أثناء تحميل الميديا: {e}")
