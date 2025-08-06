from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    API_V1_ROUTE: Optional[str] = None
    APP_ENV: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )


class GlobalConfig(BaseConfig):
    GOOGLE_API_KEY: Optional[str] = None
    PINECONE_INDEX_NAME: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    MONGO_DB: Optional[str] = None
    MONGO_URI: Optional[str] = None
    PINECONE_KEY: Optional[str] = None
    HUGGINGFACEHUB_API_TOKEN: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    API_KEY: Optional[str] = None
    SEARCH_URL: Optional[str] = None


class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict()  # env_prefix="DEV_"


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict()


class TestConfig(GlobalConfig):
    DATABASE_URL: str = "sqlite:///test.db"
    DB_FORCE_ROLL_BACK: bool = True
    JWT_SECRET_KEY: str = (
        "4598398cca0a7ecb7c7466fb30e43d4525bb3f5c59974183c8f46724e63ccee7"
    )
    JWT_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_prefix="TEST_")


# @lru_cache()
def get_config(app_env: str):
    # print(app_env)
    configs = {
        "dev": DevConfig,
        "prod": ProdConfig,
        "test": TestConfig,
        "local": DevConfig,
    }
    return configs[app_env]()


# print(f"{Path(__file__).parent.parent.parent}\.env")
# print(os.path.expanduser("~/.env"))
# print(GlobalConfig().DATABASE_URL)
# print(BaseConfig().APP_ENV)
# print(get_config(BaseConfig()))
config = get_config(BaseConfig().APP_ENV)