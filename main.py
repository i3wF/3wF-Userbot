import asyncio
import logging
import os
from time import perf_counter
from traceback import print_exc

import git
from pyrogram import Client, idle
from convopyro import Conversation
from pyrogram.enums import ParseMode

from utils.db import db
from utils.misc import script_path
from utils.scripts import CustomFormatter
from utils.config import api_id, api_hash, bot_token, string_session

if script_path != os.getcwd():
    os.chdir(script_path)

async def main():
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(
        CustomFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[stdout_handler],
    )
    
    app = Client(
        "myOwnAccount",
        sleep_threshold=30,
        api_id=api_id,
        api_hash=api_hash,
        session_string=string_session,
        lang_code="ar",
        device_model="MacBook Pro M1",
        system_version="14.3.1",
        plugins=dict(root="plugins"),
        workdir=script_path,
        parse_mode=ParseMode.HTML,
    )

    bot = Client(
        "myOwnBot",
        sleep_threshold=30,
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot_token,
        plugins=dict(root="plugins2"),
    )

    Conversation(app)
    Conversation(bot)

    await app.start()
    await bot.start()

    db.set("core", "user_id", app.me.id)
    db.set("core", "bot_username", bot.me.username)
    
    async for dialog in app.get_dialogs(limit=100):
        logging.info(f"Dialog: {dialog.chat.title}")

    await app.storage.save()

    if updater := db.get("core.updater", "restart_info"):
        try:
            if updater["type"] == "restart":
                logging.info(
                    f"{app.me.username}#{app.me.id} | Userbot succesfully restarted."
                )
                await app.edit_message_text(
                    chat_id=updater["chat_id"],
                    message_id=updater["message_id"],
                    text=f"<code>Restarted in {perf_counter() - updater['time']:.3f}s...</code>",
                )
            elif updater["type"] == "update":
                current_hash = git.Repo().head.commit.hexsha
                git.Repo().remote("origin").fetch()

                update_text = (
                    f"Userbot succesfully updated from {updater['hash'][:7]} "
                    f"to {current_hash[:7]} version."
                )

                logging.info(f"{app.me.username}#{app.me.id} | {update_text}.")
                await app.edit_message_text(
                    chat_id=updater["chat_id"],
                    message_id=updater["message_id"],
                    text=(
                        f"<code>{update_text}.\n\n"
                        f"Restarted in {perf_counter() - updater['time']:.3f}s...</code>"
                    ),
                )
        except Exception:
            print("Error when updating!")
            print_exc()

        db.remove("core.updater", "restart_info")
    else:
        logging.info(
            f"{app.me.username}#{app.me.id} on SEHSEH | Userbot succesfully started."
        )

    await idle()
    await app.stop()
    await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
