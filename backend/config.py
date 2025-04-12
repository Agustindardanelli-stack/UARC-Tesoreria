import os
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "Tesoreria API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # JWT Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "reemplazar_con_clave_secreta")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database Settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "usuario_bd")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "contraseña_bd")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "host_bd")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "nombre_bd")
    
    # CORS Settings
    CORS_ORIGINS: list = ["*"]
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()