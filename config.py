import os
from dotenv import load_dotenv

class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

    # Email settings (using Gmail SMTP as example)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("botivaai@gmail.com")  # your Gmail address
    MAIL_PASSWORD = os.getenv("Mskills123.")  # your Gmail app password
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")


