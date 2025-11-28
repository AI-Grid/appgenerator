import os
from functools import lru_cache


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://appuser:apppassword@mysql:3306/appdb",
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "changeme")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    keystore_dir: str = os.getenv("KEYSTORE_DIR", "/data/keystores")
    artifact_dir: str = os.getenv("ARTIFACT_DIR", "/data/artifacts")
    icon_dir: str = os.getenv("ICON_DIR", "/data/icons")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
