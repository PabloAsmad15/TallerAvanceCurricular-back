from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email - Resend
    RESEND_API_KEY: str
    MAIL_FROM: str = "noreply@resend.dev"
    MAIL_FROM_NAME: str = "Sistema Avance Curricular UPAO"
    DEV_EMAIL_OVERRIDE: Optional[str] = None  # Email para desarrollo
    
    # Email Legacy (opcional)
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_PORT: Optional[int] = None
    MAIL_SERVER: Optional[str] = None
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    
    # Gemini
    GEMINI_API_KEY: str
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
