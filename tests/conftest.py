import os
from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient

from modules.mysql_driver import MySQLDatabase

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

storage: MySQLDatabase = MySQLDatabase(
    database='test_' + os.getenv('MYSQL_DATABASE', 'app'),
    host=os.getenv('MYSQL_HOST', 'localhost'),
    port=int(os.getenv('MYSQL_PORT', 3306)),
    user=os.getenv('MYSQL_USER', 'root'),
    password=os.getenv('MYSQL_PASSWORD', 'password'),
    is_test=True,
)
os.environ['APP_ENV'] = 'local'  # Trick the app to avoid running with /api prefix

from main import app_
from modules import MigrationManager
from routes import v1


@pytest.fixture(scope='session', autouse=True)
def setup_once(request):
    storage.teardown_db()
    storage.init_db()
    MigrationManager(
        db_user=storage.user,
        db_password=storage.password,
        db_host=storage.host,
        db_name=storage.database,
        db_port=storage.port,
        base_dir=BASE_DIR,
    ).apply()

    def teardown():
        storage.teardown_db()

    request.addfinalizer(teardown)


@pytest.fixture(scope='function')
@asynccontextmanager
async def app():
    app_.extra['storage'] = storage
    v1.app_.extra['storage'] = storage

    client = TestClient(app_)
    app_.mount('/v1', v1.app_, 'V1')

    await storage.acquire_pool()

    yield client

    await storage.close_pool()
