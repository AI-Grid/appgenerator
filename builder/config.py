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
    android_cmdline_url: str = os.getenv(
        "ANDROID_CMDLINE_URL",
        "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip",
    )
    android_packages: list[str] = os.getenv(
        "ANDROID_PACKAGES",
        "platform-tools,platforms;android-34,build-tools;34.0.0",
    ).split(",")
    gradle_version: str = os.getenv("GRADLE_VERSION", "8.6")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
