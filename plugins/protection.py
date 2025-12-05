from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help
from utils.filters import command
from utils.db import db

enabled_ids = set(db.get("protection", "enabled_ids", default=[]))
warning_messages = {}

@Client.on_message(filters.private, group=1)
async def protection_handler(client: Client, message: Message):
    user_id = message.from_user.id
    protection_enabled = db.get("protection", "enabled")
    user_warns = db.get("warns", str(user_id))
    if not message.from_user.is_bot:
        if (
            protection_enabled
            and user_id not in enabled_ids
            and user_id != client.me.id
        ):
            user_warns = user_warns + 1 if user_warns is not None else 1
            db.set("warns", str(user_id), user_warns)
            if user_warns >= 10:
                db.remove("warns", str(user_id))
                await client.delete_messages(message.chat.id, warning_messages[user_id])
                await message.reply_text(
                    "لقد تجاوزت الحد المسموح للرسائل وهذا يسمى تكرار ولذلك تم حظرك مؤقتاً",
                    quote=True,
                )
                await client.block_user(user_id)
            else:
                if user_id in warning_messages:
                    await client.delete_messages(
                        message.chat.id, warning_messages[user_id]
                    )
                warning_msg = await message.reply_text(
                    f"انتظر لين ارد عليك ولا تسوي سبام\n\nعدد تحذيراتك: [{user_warns}/10]",
                    quote=True,
                )
                warning_messages[user_id] = warning_msg.id


@Client.on_message(
    command(["prot"])
    & filters.me
    & filters.private
    & ~filters.forwarded
    & ~filters.scheduled,
    group=2,
)
async def protection_config_handler(client: Client, message: Message):
    args = message.command[1:]
    if not args:
        return await message.edit_text(
            "<b>تكوين الحماية الحالي:</b>\n"
            f"الحماية: <code>{bool(db.get('protection', 'enabled'))}</code>\n"
        )
    result = ""
    enable_states = {"on": True, "off": False}
    if args[0] in enable_states:
        is_enable = enable_states[args[0]]
        db.set("protection", "enabled", is_enable)
        result += f"Protection {args[0]}\n"
    else:
        result += "Invalid value for enable. Should be on/off\n"
    if not result:
        return await message.edit_text(
            "<emoji id=5830218371160873658>❌</emoji><b> Invalid arguments</b>"
        )
    return await message.edit_text(result)


@Client.on_message(
    command(["enable", "e"])
    & filters.me
    & filters.private
    & ~filters.forwarded
    & ~filters.scheduled,
    group=3,
)
async def enable_command_handler(client: Client, message: Message):
    user_id = message.chat.id
    db.remove("warns", str(user_id))
    current_ids = set(db.get("protection", "enabled_ids", default=[]))
    current_ids.add(user_id)
    db.set("protection", "enabled_ids", list(current_ids))
    enabled_ids = current_ids
    if user_id in warning_messages:
        await client.delete_messages(message.chat.id, warning_messages[user_id])
        del warning_messages[user_id]
    await message.edit_text(f"تم تفعيلك الان تستطيع التحدث معي")


@Client.on_message(
    command(["disable", "d"])
    & filters.me
    & filters.private
    & ~filters.forwarded
    & ~filters.scheduled,
    group=4,
)
async def disable_command_handler(client: Client, message: Message):
    user_id = message.chat.id
    db.remove("warns", str(user_id))
    current_ids = set(db.get("protection", "enabled_ids", default=[]))
    if user_id in current_ids:
        current_ids.remove(user_id)
        db.set("protection", "enabled_ids", list(current_ids))
        enabled_ids = current_ids
    if user_id in warning_messages:
        await client.delete_messages(message.chat.id, warning_messages[user_id])
        del warning_messages[user_id]
    await message.edit_text(f"تم رفضك لاني مابيك")
    await client.block_user(user_id)


module = modules_help.add_module("protection", __file__)
module.add_command(
    "prot", "prot [on/off] to enable/disable protection private messages"
)
module.add_command("e", "to enable user in protection [on]")
module.add_command("enable", "to enable user in protection [on]")
module.add_command("d", "to block user in protection [on]")
module.add_command("disable", "to block user in protection [on]")
