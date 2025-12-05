from dotenv import dotenv_values

env = dotenv_values("./.env")


def get_env_value(key: str, to_type, default=None):
    value = env.get(key)
    if value is None:
        return default

    try:
        return to_type(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid value for {key}: {value}") from e


api_id = get_env_value("API_ID", int)
api_hash = get_env_value("API_HASH", str)
bot_token = get_env_value("BOT_TOKEN", str)
string_session = get_env_value("STRING_SESSION", str)

replies_id = get_env_value("REPLIES_ID", str)


