from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Contract Analyzer"
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    DATABASE_URL: str = "sqlite:///./contract_analyzer.db" 
    OPENAI_API_KEY: str = ""
    CLAUDE_API_KEY: str = ""
    HUGGINGFACE_API_TOKEN: str = ""
    SECRET_KEY: str = "highly_secure_secret_key_for_jwt"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_V1_STR: str = "/api/v1"

    class Config:
        env_file = ".env"

settings = Settings()
