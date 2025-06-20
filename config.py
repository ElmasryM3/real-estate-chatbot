import os

class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

