from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL=os.getenv("DATABASE_URL")
    JWT_TOKEN=os.getenv("JWT_TOKEN")
    JWT_ALGORITHM:str="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int=30
    class Config:
        env_file=".env"
        
        
settings=Settings()
