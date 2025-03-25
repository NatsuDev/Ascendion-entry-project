from contextlib import suppress
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

import aiomysql
import pymysql
from aiomysql.cursors import DictCursor
from pymysql import err as mysql_errors
from pymysql.cursors import DictCursor as SyncDictCursor

from .attr_dict import AttrDict


class _PoolContextManager:
    """
    Unused and inefficient, leave me here for a while.
    """

    def __init__(
        self,
        database: str,
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: Optional[str] = None,
    ):
        self.host: str = host
        self.port: int = port
        self.user: str = user
        self.password: str = password
        self.database = database
        self.pool: Optional[aiomysql.Pool] = None

    async def __aenter__(self) -> aiomysql.Pool:
        self.pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.database,
        )
        return self.pool

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.pool.close()


class MySQLDatabase:
    """Helper class primarily for managing database connection pool"""

    def __init__(
        self,
        database: str,
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize database.
        :param database: Database name.
        :param host: Database host.
        :param port: Database port.
        :param user: Database user.
        :param password: Database password.
        """

        self.pool: Optional[aiomysql.Pool] = None
        self.host: str = host
        self.port: int = port
        self.user: str = user
        self.password: str = password
        self.database = database
        self.extra = kwargs

    def __del__(self):
        if self.pool:
            self.pool.close()

    def init_db(self):
        """
        Creates the database if it doesn't exist.
        """
        connection = pymysql.connect(
            host=self.host, user=self.user, password=self.password, port=self.port
        )
        with connection.cursor(SyncDictCursor) as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {self.database} "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
            connection.commit()
        connection.close()

    def teardown_db(self):
        """
        Destroys the database if it exists.
        """
        connection = pymysql.connect(
            host=self.host, user=self.user, password=self.password, port=self.port
        )
        with connection.cursor(SyncDictCursor) as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {self.database};")
            connection.commit()
        connection.close()

    async def acquire_pool(self) -> bool:
        """
        Creates a new MySQL pool.
        """
        if isinstance(self.pool, aiomysql.Pool):
            with suppress(Exception):
                self.pool.close()

        self.pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.database,
            maxsize=30,
            pool_recycle=60,
        )
        return True

    async def close_pool(self) -> bool:
        """
        Closes existing MySQL pool.
        :return: True if the pool was successfully closed, False otherwise.
        """
        with suppress(Exception):
            self.pool.close()
            return True
        return False


class MySQLStorage:
    """Database connection wrapper class with helper methods for making queries"""

    def __init__(self, connection):
        self.connection = connection

    @staticmethod
    def _verify_args(args: Any) -> Tuple[Any, ...]:
        """
        Normalizes query arguments if necessary.
        :param args: Query arguments.
        :return: Normalized query arguments.
        """
        if not isinstance(args, (tuple, dict)):
            args = (args,)
        return args

    async def apply(
        self, query: str, args: Union[Tuple[Any, ...], Dict[str, Any], Any] = ()
    ) -> Any:
        """
        Executes SQL query and returns the number of affected rows.
        :param query: SQL query to execute.
        :param args: Arguments passed to the SQL query.
        :return: Number of affected rows.
        """
        args = self._verify_args(args)
        conn = self.connection
        async with conn.cursor(DictCursor) as cursor:
            try:
                await cursor.execute(query, args)
                await conn.commit()
            except mysql_errors.Error as e:
                await conn.rollback()
                raise e

            if "insert into" in query.lower():
                return cursor.lastrowid
            else:
                return cursor.rowcount

    async def apply_many(
        self, queries: List[Tuple[str, Union[Tuple[Any, ...], Dict[str, Any], Any]]]
    ) -> Any:
        """
        Executes SQL query and returns the number of affected rows.
        :param queries: A list of SQL queries and arguments to execute.
        :return: Number of affected rows.
        """
        conn = self.connection
        async with conn.cursor(DictCursor) as cursor:
            try:
                for query, args in queries:
                    args = self._verify_args(args)
                    await cursor.execute(query, args)
                await conn.commit()
                return cursor.rowcount
            except mysql_errors.Error as e:
                await conn.rollback()
                raise e

    async def select(
        self, query: str, args: Union[Tuple[Any, ...], Dict[str, Any], Any] = ()
    ) -> AsyncGenerator[Union[Dict[str, Any], "AttrDict"], None]:
        """
        Generator that yields rows.
        :param query: SQL query to execute.
        :param args: Arguments passed to the SQL query.
        :return: Yields rows one by one.
        """
        args = self._verify_args(args)
        conn = self.connection
        async with conn.cursor(DictCursor) as cursor:
            try:
                await cursor.execute(query, args)
                await conn.commit()
                while True:
                    item = await cursor.fetchone()
                    if item:
                        yield AttrDict(item)
                    else:
                        break
            except mysql_errors.Error as e:
                raise e

    async def get(
        self,
        query: str,
        args: Union[Tuple[Any, ...], Dict[str, Any], Any] = (),
        fetch_all: bool = False,
        use_attr_dict: bool = True,
    ) -> Union[bool, List[Dict[str, Any]], Dict[str, Any], "AttrDict", List["AttrDict"]]:
        """
        Get a single row or a list of rows from the database.
        :param query: SQL query to execute.
        :param args: Arguments passed to the SQL query.
        :param fetch_all: Set True if you need a list of rows instead of just a single row.
        :param use_attr_dict: Whether to use dict or AttrDict for fetched rows.
        :return: A row or a list of rows.
        """
        args = self._verify_args(args)
        conn = self.connection
        async with conn.cursor(DictCursor) as cursor:
            try:
                await cursor.execute(query, args)
                await conn.commit()

                if fetch_all:
                    if use_attr_dict:
                        return [AttrDict(row) for row in await cursor.fetchall()]
                    return await cursor.fetchall() or []
                else:
                    result = await cursor.fetchone() or {}
                    if use_attr_dict:
                        return AttrDict(result)
                    return result
            except mysql_errors.Error as e:
                raise e

    async def check(
        self, query: str, args: Union[Tuple[Any, ...], Dict[str, Any], Any] = ()
    ) -> int:
        """
        Executes SQL query and returns the number of affected rows.
        :param query: SQL query to execute.
        :param args: Arguments passed to the SQL query.
        :return: Number of affected rows.
        """
        args = self._verify_args(args)
        conn = self.connection
        async with conn.cursor(DictCursor) as cursor:
            try:
                await cursor.execute(query, args)
                await conn.commit()

                return cursor.rowcount
            except mysql_errors.Error as e:
                raise e
