from pyrogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    InlineQuery,
)
from pyrogram.enums import ChatType, ParseMode
from pyrogram import Client, filters
from utils.db import RedisHandler
from datetime import datetime
from utils.db import db

import pytz
import os

redis_handler = RedisHandler()


async def format_date(timestamp):
    try:
        if isinstance(timestamp, str):
            try:
                datetime_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                return datetime_obj.strftime("%Y-%m-%d %I:%M %p")
            except ValueError:
                try:
                    timestamp = float(timestamp)
                except ValueError:
                    return "غير متاح"

        if isinstance(timestamp, (int, float)):
            riyadh_timezone = pytz.timezone("Asia/Riyadh")
            datetime_obj = datetime.fromtimestamp(timestamp, riyadh_timezone)
            formatted_time = datetime_obj.strftime("%Y-%m-%d %I:%M %p")
            return formatted_time

        elif isinstance(timestamp, datetime):
            riyadh_timezone = pytz.timezone("Asia/Riyadh")
            datetime_obj = timestamp.astimezone(riyadh_timezone)
            formatted_time = datetime_obj.strftime("%Y-%m-%d %I:%M %p")
            return formatted_time
        else:
            return "غير متاح"
    except Exception as e:
        print(f"Error: {e}")
        return "غير متاح"


async def fetch_user_data(user_id):
    user_key = f"user:{user_id}"
    user_data = redis_handler.hgetall(user_key)
    user_info = {
        "user_id": user_id,
        "username": user_data.get("username", "غير متاح"),
        "first_name": user_data.get("first_name", "غير متاح"),
        "last_name": user_data.get("last_name", "غير متاح"),
        "previous_usernames": redis_handler.lrange(f"{user_key}:usernames", 0, -1),
        "previous_first_names": redis_handler.lrange(f"{user_key}:first_names", 0, -1),
        "previous_last_names": redis_handler.lrange(f"{user_key}:last_names", 0, -1),
    }
    messages = []
    message_types = [ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP]

    for message_type in message_types:
        keys = redis_handler.keys(f"{message_type}:{user_id}:*")
        for key in keys:
            message_data = redis_handler.hgetall(key)
            formatted_date = await format_date(message_data.get("date"))
            messages.append(
                {
                    "message_id": message_data.get("message_id"),
                    "date": formatted_date,
                    "message_type": message_data.get("message_type"),
                    "text": message_data.get("text"),
                    "caption": message_data.get("caption"),
                    "file_id": message_data.get("file_id"),
                }
            )

        json_filename = f"{user_id}_data.json"
    with open(json_filename, "w", encoding="utf-8") as json_file:
        import json

        json.dump(
            {"user_info": user_info, "messages": messages},
            json_file,
            ensure_ascii=False,
            indent=4,
        )

    return json_filename


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

    buttons = []
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
        if file_id and file_id != "":
            download_button = InlineKeyboardButton(
                "🔗 تحميل الميديا",
                callback_data=f"dm_{message_type}_{user_id}_{message_data.get('message_id')}",
            )
            buttons.append(download_button)

        result += message_info
        result += "\n--------------------------\n"

    total_pages = len(keys) // messages_per_page + (
        1 if len(keys) % messages_per_page > 0 else 0
    )

    if total_pages > 1:
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
        message_type_formatted = "group"
    else:
        message_type_ar = "الخاص"
        message_type_formatted = "private"

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

    buttons = []

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
        if file_id and file_id != "":
            download_button = InlineKeyboardButton(
                "🔗 تحميل الميديا",
                callback_data=f"dm_{message_type_formatted}_{user_id}_{message_data.get('message_id')}",
            )
            buttons.append(download_button)

        result += message_info
        result += "\n--------------------------\n"

    total_pages = len(keys_to_display) // messages_per_page + (
        1 if len(keys_to_display) % messages_per_page > 0 else 0
    )

    if total_pages > 1:
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


@Client.on_inline_query(group=2)
async def inline_checker(_, query: InlineQuery):
    if query.from_user.id != db.get("core", "user_id"): return
    string = query.query.lower()
    if string.startswith("check"):
        parts = string.split()
        if len(parts) < 2:
            await query.answer(
                results=[
                    InlineQueryResultArticle(
                        title="⚠️ خطأ: لم يتم إدخال معرف",
                        input_message_content=InputTextMessageContent(
                            "⚠️ الرجاء إدخال معرف المستخدم بعد الأمر. مثال: `check 12345678`"
                        ),
                        description="أدخل المعرف بشكل صحيح.",
                    )
                ],
                cache_time=0,
            )
            return

        user_id = parts[1]
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
                        "� تحميل جميع الرسائل", callback_data=f"get_messages:{user_id}"
                    )
                ],
            ]
        )

        await query.answer(
            results=[
                InlineQueryResultArticle(
                    title="🔍 اختر نوع الاستعلام",
                    input_message_content=InputTextMessageContent(
                        "اختر من القائمة أدناه:"
                    ),
                    reply_markup=reply_markup,
                )
            ],
            cache_time=0,
        )


@Client.on_callback_query(group=1313)
async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split(":")
    if callback_query.from_user.id != db.get("core", "user_id"): return
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

        if callback_query.inline_message_id:
            await client.edit_inline_text(
                inline_message_id=callback_query.inline_message_id,
                text=result,
                reply_markup=reply_markup,
                parse_mode=ParseMode.DISABLED,
            )
        else:
            await client.edit_inline_text(
                inline_message_id=callback_query.inline_message_id,
                text=result,
                reply_markup=reply_markup,
                parse_mode=ParseMode.DISABLED,
            )

    elif data[0] in ["private", "group"]:
        message_type = ChatType.PRIVATE if data[0] == "private" else data[0]
        user_id = data[1]
        result, reply_markup = await fetch_messages(user_id, message_type)

        if callback_query.inline_message_id:
            await client.edit_inline_text(
                inline_message_id=callback_query.inline_message_id,
                text=result,
                reply_markup=reply_markup,
                parse_mode=ParseMode.DISABLED,
            )
        else:
            await client.edit_inline_text(
                inline_message_id=callback_query.inline_message_id,
                text=result,
                reply_markup=reply_markup,
                parse_mode=ParseMode.DISABLED,
            )

    elif data[0] == "get_messages":
        user_id = data[1]
        json_filename = await fetch_user_data(user_id)

        if json_filename and os.path.exists(json_filename):
            await client.edit_inline_text(
                inline_message_id=callback_query.inline_message_id,
                text="تم ارسالها في الخاص نجاح",
                parse_mode=ParseMode.DISABLED,
            )
            await client.send_document(
                chat_id=callback_query.from_user.id,
                document=json_filename,
                caption="📁 جميع الرسائل تم تجميعها في هذا الملف.",
            )
            os.remove(json_filename)
        else:
            await callback_query.message.reply("🚫 لا توجد رسائل متاحة.")
