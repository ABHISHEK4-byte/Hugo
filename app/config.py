import os

APP_NAME = "Hugo"
APP_VERSION = "0.2.0"
DATA_DIR = "data"
STATE_FILE = "state.json"
DEFAULT_IDENTITY = "Abhishek a professional software eng"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL = os.getenv("HUGO_DEFAULT_MODEL", "gpt-4o-mini")
