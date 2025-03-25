from fastapi import Request

from modules.mysql_driver import MySQLStorage


async def get_storage(request: Request) -> MySQLStorage:
    """
    Get storage instance.
    :param request: FastAPI request.
    :return: Storage instance.
    """
    storage = request.app.extra["storage"]
    if storage.extra.get("is_test"):
        await storage.acquire_pool()
    async with storage.pool.acquire() as connection:
        yield MySQLStorage(connection)
