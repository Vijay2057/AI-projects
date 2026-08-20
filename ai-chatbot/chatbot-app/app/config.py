import os
from dotenv import load_dotenv


load_dotenv()

class Settings:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE_URl = "postgresql+asyncpg://postgres:postgres@localhost:5432/chatbot"



settings = Settings()