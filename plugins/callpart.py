from pyrogram import Client, filters, enums
from pyrogram.types import Message
from main import userbot1


@Client.on_message(filters.regex(r"^من في الكول$") & filters.group, group=15)
async def whoiscall(client: Client, m: Message):
    async def fetch_participants(chat_id):
        try:
            participants = [member async for member in client.get_call_members(chat_id)]
            return participants
        except ValueError as e:
            if str(e) == "There is no active call in this chat.":
                await m.edit_text("لا توجد مكالمة نشطة في هذه الدردشة.")
                return None
            raise e

    try:
        participants = await fetch_participants(m.chat.id)
        if participants is None:
            return
    except Exception as e:
        return await m.edit_text(f"**خطأ :** `{e}`")
    if not participants:
        return await m.edit_text("لايوجد اي عضو بالمكالمة")

    reply_text = "⌯ الاعضاء الموجودين في المكالمة : \n\n"

    for member in participants:
        status = "ساكت" if member.is_muted else "يتكلم"
        mention = f"[{member.chat.first_name}](tg://user?id={member.chat.id})"
        reply_text += f"⌯ - {mention} › {status}\n"
    
    reply_text += f"\n⌯ عدد الموجودين : {len(participants)}"

    await m.edit_text(reply_text, parse_mode=enums.ParseMode.MARKDOWN)
