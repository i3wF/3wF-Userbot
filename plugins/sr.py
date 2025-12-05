from pyrogram import Client, filters
from pyrogram.types import Message
import re
import os

from utils.misc import modules_help
from utils.filters import command
from utils.scripts import get_args


def parse_tg_link(link):
    """Parse Telegram message link to extract chat_id and message_id"""

    private_pattern = r'tg://openmessage\?user_id=(\d+)&message_id=(\d+)'
    private_group_pattern = r'https://t\.me/c/(\d+)/(\d+)'
    public_pattern = r'https://t\.me/([^/]+)/(\d+)'
    
    private_match = re.match(private_pattern, link)
    if private_match:
        return int(private_match.group(1)), [int(private_match.group(2))], "private"
    
    private_group_match = re.match(private_group_pattern, link)
    if private_group_match:
        return private_group_match.group(1), [int(private_group_match.group(2))], "private_group"
    
    public_match = re.match(public_pattern, link)
    if public_match:
        return public_match.group(1), [int(public_match.group(2))], "public"

    return None, None, None


@Client.on_message(command("sr") & filters.me)
async def save_restriction_content(client: Client, message: Message):
    args, _ = get_args(message)
    
    if not args:
        return await message.edit("<b>Please provide a link to save restriction content.</b>\nUsage: <code>.sr link</code>")
    
    link = args[0]
    await message.edit(f"<b>Processing link...</b>")

    chat_id, message_id, chat_type = parse_tg_link(link)
    
    if chat_id is None or message_id is None:
        return await message.edit("<b>Invalid link format!</b>\nPlease provide a valid Telegram message link.")
    
    try:
        if chat_type == "private":
            target_messages = await client.get_messages(chat_id, message_ids=message_id)
            target_message = target_messages[0] if target_messages else None
        elif chat_type == "public":
            chat = await client.get_chat(chat_id)
            target_messages = await client.get_messages(chat.id, message_ids=message_id)
            target_message = target_messages[0] if target_messages else None
        elif chat_type == "private_group":
            chat_id_int = int(f"-100{chat_id}")
            target_messages = await client.get_messages(chat_id_int, message_ids=message_id)
            target_message = target_messages[0] if target_messages else None
        
        if not target_message:
            return await message.edit("<b>Message not found!</b>\nThe message may have been deleted or is inaccessible.")

        if not target_message.media:
            return await message.edit("<b>This message doesn't contain any media!</b>\nOnly messages with media can be saved.")

        downloads_dir = "downloads"
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)

        file_path = await client.download_media(
            target_message,
            file_name=f"{downloads_dir}/"
        )
        
        try:
            if target_message.photo:
                await client.send_photo(
                    chat_id="me",
                    photo=file_path,
                    caption=f"<b>Content saved from:</b> {link}"
                )
            elif target_message.video:
                await client.send_video(
                    chat_id="me",
                    video=file_path,
                    caption=f"<b>Content saved from:</b> {link}"
                )
            elif target_message.audio:
                await client.send_audio(
                    chat_id="me",
                    audio=file_path,
                    caption=f"<b>Content saved from:</b> {link}"
                )
            elif target_message.document:
                await client.send_document(
                    chat_id="me",
                    document=file_path,
                    caption=f"<b>Content saved from:</b> {link}"
                )
            elif target_message.animation:
                await client.send_animation(
                    chat_id="me",
                    animation=file_path,
                    caption=f"<b>Content saved from:</b> {link}"
                )
            elif target_message.voice:
                await client.send_voice(
                    chat_id="me",
                    voice=file_path,
                    caption=f"<b>Content saved from:</b> {link}"
                )
            elif target_message.video_note:
                await client.send_video_note(
                    chat_id="me",
                    video_note=file_path
                )
            else:
                await client.send_document(
                    chat_id="me",
                    document=file_path,
                    caption=f"<b>Content saved from:</b> {link}"
                )
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        await message.edit(f"<b>Content saved successfully to saved messages!</b>\nSource: {link}")
        
    except Exception as e:
        await message.edit(f"<b>An error occurred:</b>\n<code>{str(e)}</code>")
        

module = modules_help.add_module("save restriction content", __file__)
module.add_command(
    command="sr",
    description="save restriction content by link",
    
)