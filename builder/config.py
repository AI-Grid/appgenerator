import os
from functools import lru_cache


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://appuser:apppassword@mysql:3306/appdb",
    )
    keystore_dir: str = os.getenv("KEYSTORE_DIR", "/data/keystores")
    artifact_dir: str = os.getenv("ARTIFACT_DIR", "/data/artifacts")
    build_work_dir: str = os.getenv("BUILD_WORK_DIR", "/data/builds")
    android_sdk_root: str = os.getenv("ANDROID_SDK_ROOT", "/opt/android-sdk")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
