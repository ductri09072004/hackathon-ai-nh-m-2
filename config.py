import os

from dotenv import load_dotenv

load_dotenv()  # fills os.environ from .env; real environment variables win


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name) or default
