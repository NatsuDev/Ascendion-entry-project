import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from modules import MySQLDatabase

SRC_DIR: str = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR: str = os.path.dirname(SRC_DIR)
ENVIRONMENT = os.getenv("APP_ENV", "local")
load_dotenv(os.path.join(ROOT_DIR, "env", f".env.{ENVIRONMENT}"))
print(os.path.abspath(os.path.join(ROOT_DIR, "env", f".env.{ENVIRONMENT}")))
print(ENVIRONMENT)
print(os.environ)


class MariaDBSettings(BaseModel):
    host: str = Field(default="127.0.0.1")
    user: str = Field()
    password: str = Field()
    name: str = Field(default="app")
    port: int = Field(default=3306)


class AppSettings(BaseModel):
    title: str = Field(default="Entry project")
    version: str = Field(default="1.0.0")
    port: int = Field(default=8080)
    keep_alive_timeout: int = Field(default=5)
    host: str = Field(default="0.0.0.0")  # nosec B104


class Settings(BaseSettings):
    db: MariaDBSettings = Field()
    disable_swagger_docs: bool = Field(default=False)
    disable_redoc_docs: bool = Field(default=True)
    app: AppSettings = Field(default=AppSettings())
    jwt_secret: str = Field()
    jwt_expires_minutes: int = Field(default=720)  # 12 hours default

    class Config:
        env_nested_delimiter = "__"


SETTINGS = Settings()


STORAGE: MySQLDatabase = MySQLDatabase(
    database=SETTINGS.db.name,
    host=SETTINGS.db.host,
    port=SETTINGS.db.port,
    user=SETTINGS.db.user,
    password=SETTINGS.db.password,
)
