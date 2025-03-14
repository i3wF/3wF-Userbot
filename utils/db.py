import threading
import asyncio
import sqlite3
import redis
import json

import aiosqlite
import redis.exceptions

from utils.config import db_name


class RedisHandler:
    def __init__(self, redis_host="localhost", redis_port=6379, redis_db=0):
        self.redis_client = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
            charset="utf-8",
        )

    def set_key(self, redis_key, value):
        return self.redis_client.set(redis_key, value)

    def get_key(self, redis_key):
        return self.redis_client.get(redis_key)

    def delete_key(self, redis_key):
        return self.redis_client.delete(redis_key)

    def hset(self, redis_key, mapping):
        if not isinstance(mapping, dict):
            raise ValueError("Mapping must be a dictionary.")
        self.redis_client.hset(redis_key, mapping=mapping)

    def lpush(self, redis_key, value):
        self.redis_client.lpush(redis_key, value)

    def hgetall(self, redis_key):
        return self.redis_client.hgetall(redis_key)

    def keys(self, pattern="*"):
        return self.redis_client.keys(pattern)

    def hget(self, redis_key, field):
        return self.redis_client.hget(redis_key, field)

    def lrange(self, redis_key, start=0, end=-1):
        return self.redis_client.lrange(redis_key, start, end)

    def is_hash(self, redis_key):
        try:
            self.redis_client.hgetall(redis_key)
            return True
        except redis.exceptions.ResponseError:
            return False

    def is_list(self, redis_key):
        try:
            self.redis_client.lrange(redis_key, 0, 0)
            return True
        except redis.exceptions.ResponseError:
            return False


class Database:
    def get(self, module: str, variable: str, default=None):
        raise NotImplementedError

    def set(self, module: str, variable: str, value):
        raise NotImplementedError

    def remove(self, module: str, variable: str):
        raise NotImplementedError

    def get_collection(self, module: str) -> dict:
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


class SqliteDatabase(Database):
    def __init__(self, file):
        self._conn = sqlite3.connect(file, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._cursor = self._conn.cursor()
        self._lock = threading.Lock()

    @staticmethod
    def _parse_row(row: sqlite3.Row):
        parse_func = {
            "bool": lambda x: x == "1",
            "int": int,
            "str": lambda x: x,
            "json": json.loads,
        }
        return parse_func[row["type"]](row["val"])

    def _create_table(self, module: str):
        sql = f"""
        CREATE TABLE IF NOT EXISTS '{module}' (
        var TEXT UNIQUE NOT NULL,
        val TEXT NOT NULL,
        type TEXT NOT NULL
        )
        """
        self._cursor.execute(sql)
        self._conn.commit()

    def _execute(self, module: str, sql, params=None):
        with self._lock:
            try:
                return self._cursor.execute(sql, params)
            except sqlite3.OperationalError as e:
                if str(e).startswith("no such table"):
                    self._create_table(module)
                    return self._cursor.execute(sql, params)
                raise e from None

    def get(self, module: str, variable: str, default=None):
        cur = self._execute(
            module, f"SELECT * FROM '{module}' WHERE var=:var", {"var": variable}
        )
        row = cur.fetchone()
        return default if row is None else self._parse_row(row)

    def set(self, module: str, variable: str, value) -> bool:
        sql = f"""
        INSERT INTO '{module}' VALUES ( :var, :val, :type )
        ON CONFLICT (var) DO
        UPDATE SET val=:val, type=:type WHERE var=:var
        """

        if isinstance(value, bool):
            val = "1" if value else "0"
            typ = "bool"
        elif isinstance(value, str):
            val = value
            typ = "str"
        elif isinstance(value, int):
            val = str(value)
            typ = "int"
        else:
            val = json.dumps(value)
            typ = "json"

        self._execute(module, sql, {"var": variable, "val": val, "type": typ})
        self._conn.commit()

        return True

    def remove(self, module: str, variable: str):
        sql = f"DELETE FROM '{module}' WHERE var=:var"
        self._execute(module, sql, {"var": variable})
        self._conn.commit()

    def get_collection(self, module: str) -> dict:
        sql = f"SELECT * FROM '{module}'"
        cur = self._execute(module, sql)

        return {row["var"]: self._parse_row(row) for row in cur}

    def close(self):
        self._conn.commit()
        self._conn.close()


class AioSqliteDatabase(Database):
    def __init__(self, file=db_name):
        self._file = file
        self._conn = None

    async def _connect(self):
        self._conn = await aiosqlite.connect(self._file)
        self._conn.row_factory = aiosqlite.Row
        self._cursor = await self._conn.cursor()
        self._lock = asyncio.Lock()

    @staticmethod
    def _parse_row(row: aiosqlite.Row):
        parse_func = {
            "bool": lambda x: x == "1",
            "int": int,
            "str": lambda x: x,
            "json": json.loads,
        }
        return parse_func[row["type"]](row["val"])

    async def _create_table(self, module: str):
        sql = f"""
        CREATE TABLE IF NOT EXISTS '{module}' (
        var TEXT UNIQUE NOT NULL,
        val TEXT NOT NULL,
        type TEXT NOT NULL
        )
        """
        self._cursor.execute(sql)
        self._conn.commit()

    async def _execute(self, module: str, *args, **kwargs) -> aiosqlite.Cursor:
        try:
            return await self._cursor.execute(*args, **kwargs)
        except aiosqlite.OperationalError as e:
            if str(e).startswith("no such table"):
                await self._create_table(module)
                return await self._cursor.execute(*args, **kwargs)
            raise e from None

    async def get(self, module: str, variable: str, default=None):
        if not self._conn:
            await self._connect()
        sql = f"SELECT * FROM '{module}' WHERE var=:var"
        cur = await self._execute(module, sql, {"var": variable})

        row = await cur.fetchone()
        result = default if row is None else self._parse_row(row)
        await self.close()
        return result

    async def set(self, module: str, variable: str, value) -> bool:
        if not self._conn:
            await self._connect()
        sql = f"""
        INSERT INTO '{module}' VALUES ( :var, :val, :type )
        ON CONFLICT (var) DO
        UPDATE SET val=:val, type=:type WHERE var=:var
        """

        if isinstance(value, bool):
            val = "1" if value else "0"
            typ = "bool"
        elif isinstance(value, str):
            val = value
            typ = "str"
        elif isinstance(value, int):
            val = str(value)
            typ = "int"
        else:
            val = json.dumps(value)
            typ = "json"

        await self._execute(module, sql, {"var": variable, "val": val, "type": typ})
        await self._conn.commit()
        await self.close()
        return True

    async def remove(self, module: str, variable: str):
        if not self._conn:
            await self._connect()
        sql = f"DELETE FROM '{module}' WHERE var=:var"
        await self._execute(module, sql, {"var": variable})
        await self._conn.commit()
        await self.close()

    async def get_collection(self, module: str) -> dict:
        if not self._conn:
            await self._connect()
        sql = f"SELECT * FROM '{module}'"
        cur = await self._execute(module, sql)
        result = {row["var"]: self._parse_row(row) async for row in cur}
        await self.close()
        return result

    async def close(self):
        await self._conn.commit()
        await self._cursor.close()
        await self._conn.close()
        self._conn = None


db = SqliteDatabase(db_name)
