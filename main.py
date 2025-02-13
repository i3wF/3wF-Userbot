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
from dotenv import dotenv_values
from utils.misc import script_path
from utils.scripts import CustomFormatter

if script_path != os.getcwd():
    os.chdir(script_path)


def get_env_value(key: str, to_type, default=None):
    value = env.get(key)
    if value is None:
        return default
    try:
        return to_type(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid value for {key}: {value}") from e


env = dotenv_values("./.env")


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
    STRING_SESSION = get_env_value("STRING_SESSION", str)
    TOKEN = get_env_value("TOKEN", str)
    API_ID = get_env_value("API_ID", int)
    API_HASH = get_env_value("API_HASH", str)
    app = Client(
        "myOwnAccount",
        sleep_threshold=30,
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=STRING_SESSION,
        lang_code="ar",
        device_model="MacBook Pro M1",
        system_version="14.3.1",
        plugins=dict(root="plugins"),
        workdir=script_path,
        parse_mode=ParseMode.HTML,
    )

    app2 = Client(
        "myOwnBot",
        sleep_threshold=30,
        bot_token=TOKEN,
        api_id=API_ID,
        api_hash=API_HASH,
        plugins=dict(root="plugins2"),
    )

    Conversation(app)
    Conversation(app2)

    await app.start()
    async for dialog in app.get_dialogs(limit=100):
        logging.info(f"Dialog: {dialog.chat.title}")

    await app.storage.save()
    await app2.start()

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
    await app2.stop()


if __name__ == "__main__":
    asyncio.run(main())
