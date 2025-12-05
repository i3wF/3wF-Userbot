import redis.exceptions
import threading
import logging
import sqlite3
import redis
import json
import time
from dotenv import dotenv_values

from typing import Any, Dict, Optional, List
from contextlib import contextmanager

env = dotenv_values("./.env")
db_name = env.get("DB_NAME", "database")
if not db_name.endswith('.db'):
    db_name = f"{db_name}.db"


class RedisHandler:
    def __init__(self, redis_host="localhost", redis_port=6379, redis_db=0):
        self.redis_client = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
            encoding="utf-8", 
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
    _instance = None
    _lock_instance = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock_instance:
            if cls._instance is None:
                cls._instance = super(SqliteDatabase, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, file: str):
        if self._initialized:
            return
            
        self._file = file
        self._conn = None
        self._cursor = None
        self._lock = threading.Lock()
        self._logger = logging.getLogger(__name__)
        self._connection_pool = []
        self._max_pool_size = 5
        self._current_pool_size = 0
        self._pool_lock = threading.Lock()
        self._connect()
        self._precreate_common_tables()
        self._initialized = True
    
    def _connect(self) -> None:
        """Establish database connection with retry logic and WAL mode"""
        max_retries = 5
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                self._conn = sqlite3.connect(
                    self._file,
                    check_same_thread=False,
                    timeout=60.0,
                    isolation_level=None
                )
                self._conn.row_factory = sqlite3.Row
                self._cursor = self._conn.cursor()
                self._conn.execute("PRAGMA journal_mode=WAL")

                self._conn.execute("PRAGMA busy_timeout=60000")

                self._conn.execute("PRAGMA synchronous=NORMAL")
                self._conn.execute("PRAGMA cache_size=10000")
                self._conn.execute("PRAGMA temp_store=MEMORY")
                
                self._logger.info(f"Database connection established to {self._file} with WAL mode")
                return
            except sqlite3.Error as e:
                self._logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise sqlite3.Error(f"Failed to connect to database after {max_retries} attempts: {e}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool or create a new one with WAL mode"""
        with self._pool_lock:
            if self._connection_pool:
                return self._connection_pool.pop()
            elif self._current_pool_size < self._max_pool_size:
                self._current_pool_size += 1
                try:
                    conn = sqlite3.connect(
                        self._file,
                        check_same_thread=False,
                        timeout=60.0,
                        isolation_level=None
                    )
                    conn.row_factory = sqlite3.Row

                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA busy_timeout=60000")
                    conn.execute("PRAGMA synchronous=NORMAL")
                    conn.execute("PRAGMA cache_size=10000")
                    conn.execute("PRAGMA temp_store=MEMORY")
                    
                    return conn
                except sqlite3.Error as e:
                    self._current_pool_size -= 1
                    raise e
            else:
                time.sleep(0.2)
                return self._get_connection()
    
    def _return_connection(self, conn: sqlite3.Connection) -> None:
        """Return a connection to the pool"""
        with self._pool_lock:
            try:
                conn.execute("SELECT 1")
                self._connection_pool.append(conn)
            except sqlite3.Error:
                try:
                    conn.close()
                except:
                    pass
                self._current_pool_size -= 1
    
    @contextmanager
    def _get_cursor(self):
        """Context manager for cursor access with automatic error handling and connection pooling"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                self._return_connection(conn)
        except sqlite3.Error as e:
            self._logger.error(f"Database error: {e}")
            raise

    @staticmethod
    def _parse_row(row: Optional[sqlite3.Row]) -> Any:
        """Parse a database row into the appropriate Python type"""
        if row is None:
            return None
            
        parse_func = {
            "bool": lambda x: x == "1",
            "int": int,
            "float": float,
            "str": lambda x: x,
            "json": json.loads,
            "datetime": lambda x: time.strptime(x, "%Y-%m-%d %H:%M:%S"),
        }
        
        try:
            row_type = row["type"]
            row_val = row["val"]
            
            if row_type not in parse_func:
                raise ValueError(f"Unsupported data type: {row_type}")
                
            return parse_func[row_type](row_val)
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logging.error(f"Error parsing row: {e}")
            raise ValueError(f"Failed to parse row: {e}")

    def _create_table(self, module: str) -> None:
        """Create a table for a specific module if it doesn't exist"""
        if not module.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError(f"Invalid module name: {module}")
            
        sql = f"""
        CREATE TABLE IF NOT EXISTS '{module}' (
        var TEXT UNIQUE NOT NULL,
        val TEXT NOT NULL,
        type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                with self._lock:
                    cursor = self._conn.cursor()
                    cursor.execute(sql)
                    self._conn.commit()
                    cursor.close()
                    self._logger.debug(f"Table '{module}' created or verified")
                    return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    self._logger.warning(f"Database locked when creating table '{module}', retrying ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                self._logger.error(f"Failed to create table '{module}': {e}")
                raise
            except sqlite3.Error as e:
                self._logger.error(f"Failed to create table '{module}': {e}")
                raise
    
    def _precreate_common_tables(self) -> None:
        """Pre-create commonly used tables to avoid runtime lag"""
        common_tables = ['history', 'core', 'config', 'cache', 'core.main']
        
        try:
            with self._lock:
                cursor = self._conn.cursor()
                try:
                    for table in common_tables:
                        sql = f"""
                        CREATE TABLE IF NOT EXISTS '{table}' (
                        var TEXT UNIQUE NOT NULL,
                        val TEXT NOT NULL,
                        type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        """
                        cursor.execute(sql)
                    self._conn.commit()
                    self._logger.debug(f"Pre-created common tables: {', '.join(common_tables)}")
                finally:
                    cursor.close()
        except sqlite3.Error as e:
            self._logger.error(f"Failed to pre-create common tables: {e}")

    def _execute(self, module: str, sql: str, params: Optional[Dict[str, Any]] = None) -> sqlite3.Cursor:
        """Execute SQL with automatic table creation and error handling with retry logic"""
        if not module.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError(f"Invalid module name: {module}")
            
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                with self._get_cursor() as cursor:
                    try:
                        self._logger.debug(f"Executing SQL for module '{module}'")
                        return cursor.execute(sql, params or {})
                    except sqlite3.OperationalError as e:
                        if "no such table" in str(e).lower():
                            self._logger.debug(f"Table '{module}' not found, creating it")
                            self._create_table(module)
                            return cursor.execute(sql, params or {})
                        elif "database is locked" in str(e).lower() and attempt < max_retries - 1:
                            self._logger.warning(f"Database locked during execution for '{module}', retrying ({attempt + 1}/{max_retries})")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                        self._logger.error(f"SQL execution error: {e}")
                        raise
                    except sqlite3.Error as e:
                        self._logger.error(f"Database error during execution: {e}")
                        raise
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay)
                retry_delay *= 2

    def get(self, module: str, variable: str, default: Any = None) -> Any:
        """Retrieve a value from the database with retry logic"""
        if not variable or not isinstance(variable, str):
            raise ValueError("Variable name must be a non-empty string")
            
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                cur = self._execute(
                    module,
                    f"SELECT * FROM '{module}' WHERE var=:var",
                    {"var": variable}
                )
                row = cur.fetchone()
                result = default if row is None else self._parse_row(row)
                self._logger.debug(f"Retrieved {module}.{variable}: {result}")
                return result
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    self._logger.warning(f"Database locked when getting {module}.{variable}, retrying ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                self._logger.error(f"Error getting {module}.{variable}: {e}")
                return default
            except Exception as e:
                self._logger.error(f"Error getting {module}.{variable}: {e}")
                return default

    def set(self, module: str, variable: str, value: Any) -> bool:
        """Store a value in the database with retry logic"""
        if not variable or not isinstance(variable, str):
            raise ValueError("Variable name must be a non-empty string")
            
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                sql = f"""
                INSERT INTO '{module}' (var, val, type)
                VALUES (:var, :val, :type)
                ON CONFLICT(var) DO UPDATE SET
                val=:val,
                type=:type,
                updated_at=CURRENT_TIMESTAMP
                WHERE var=:var
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
                elif isinstance(value, float):
                    val = str(value)
                    typ = "float"
                elif hasattr(value, 'strftime'):
                    val = value.strftime("%Y-%m-%d %H:%M:%S")
                    typ = "datetime"
                else:
                    val = json.dumps(value)
                    typ = "json"

                with self._get_cursor() as cursor:
                    cursor.execute(sql, {"var": variable, "val": val, "type": typ})
                
                self._logger.debug(f"Stored {module}.{variable} ({typ}): {val}")
                return True
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    self._logger.warning(f"Database locked when setting {module}.{variable}, retrying ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                self._logger.error(f"Error setting {module}.{variable}: {e}")
                return False
            except Exception as e:
                self._logger.error(f"Error setting {module}.{variable}: {e}")
                return False

    def remove(self, module: str, variable: str) -> bool:
        """Remove a variable from the database"""
        if not variable or not isinstance(variable, str):
            raise ValueError("Variable name must be a non-empty string")
            
        try:
            sql = f"DELETE FROM '{module}' WHERE var=:var"
            self._execute(module, sql, {"var": variable})
            self._conn.commit()
            self._logger.debug(f"Removed {module}.{variable}")
            return True
        except Exception as e:
            self._logger.error(f"Error removing {module}.{variable}: {e}")
            return False

    def get_collection(self, module: str) -> Dict[str, Any]:
        """Retrieve all variables for a module as a dictionary"""
        try:
            sql = f"SELECT * FROM '{module}'"
            cur = self._execute(module, sql)
            result = {row["var"]: self._parse_row(row) for row in cur}
            self._logger.debug(f"Retrieved collection for {module}: {len(result)} items")
            return result
        except Exception as e:
            self._logger.error(f"Error getting collection for {module}: {e}")
            return {}

    def batch_set(self, module: str, data: Dict[str, Any]) -> bool:
        """Set multiple values in a single transaction"""
        if not data:
            return True
            
        try:
            with self._lock:
                self._conn.execute("BEGIN TRANSACTION")
                try:
                    for variable, value in data.items():
                        self.set(module, variable, value)
                    self._conn.commit()
                    self._logger.debug(f"Batch set {len(data)} items for {module}")
                    return True
                except Exception as e:
                    self._conn.rollback()
                    self._logger.error(f"Batch set failed, rolled back: {e}")
                    return False
        except Exception as e:
            self._logger.error(f"Error in batch set for {module}: {e}")
            return False

    def batch_remove(self, module: str, variables: List[str]) -> bool:
        """Remove multiple variables in a single transaction"""
        if not variables:
            return True
            
        try:
            with self._lock:
                self._conn.execute("BEGIN TRANSACTION")
                try:
                    for variable in variables:
                        self.remove(module, variable)
                    self._conn.commit()
                    self._logger.debug(f"Batch removed {len(variables)} items from {module}")
                    return True
                except Exception as e:
                    self._conn.rollback()
                    self._logger.error(f"Batch remove failed, rolled back: {e}")
                    return False
        except Exception as e:
            self._logger.error(f"Error in batch remove for {module}: {e}")
            return False

    def close(self) -> None:
        """Close all database connections in the pool"""
        try:
            if self._conn:
                self._conn.commit()
                self._conn.close()
                self._logger.info("Main database connection closed")
            
            with self._pool_lock:
                for conn in self._connection_pool:
                    try:
                        conn.close()
                    except sqlite3.Error as e:
                        self._logger.warning(f"Error closing pooled connection: {e}")
                
                self._connection_pool.clear()
                self._current_pool_size = 0
                self._logger.info("All pooled connections closed")
        except sqlite3.Error as e:
            self._logger.error(f"Error closing database: {e}")
            raise

db = SqliteDatabase(db_name)
