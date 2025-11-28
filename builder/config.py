import os
from functools import lru_cache


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://appuser:apppassword@mysql:3306/appdb",
    )
    keystore_dir: str = os.getenv("KEYSTORE_DIR", "/data/keystores")
    artifact_dir: str = os.getenv("ARTIFACT_DIR", "/data/artifacts")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
