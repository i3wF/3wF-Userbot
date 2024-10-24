from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import Client
from pyrogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineQuery,
)


@Client.on_inline_query(group=2)
async def inline(client: Client, query: InlineQuery):
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
                    thumb_url=client.me.photo,
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
                    thumb_url=client.me.photo,
                ),
            ]
        )
