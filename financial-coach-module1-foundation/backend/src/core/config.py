from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Financial Coach"
    OPENROUTER_API_KEY: str = ""
    DATABASE_URL: str = ""

settings = Settings()
