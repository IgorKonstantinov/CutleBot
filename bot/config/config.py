from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    RANDOM_SLEEP: list[int] = [3, 5]
    WAITING_SLEEP: list[int] = [3600, 7200]

    AUTO_UPGRADE: bool = True
    AUTO_TASK: bool = True
    AUTO_TAP: bool = True

    APPLY_DAILY_BOOST: bool = False
    USE_PROXY_FROM_FILE: bool = False

settings = Settings()
