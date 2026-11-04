import os
import pytz
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1fPCCECo7NI_oYgOq21LMpKtmfbWTI5lY3K_a238lYWk")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Karachi")
LOCAL_TZ = pytz.timezone(TIMEZONE)

BUSINESS_START_HOUR = 9
BUSINESS_END_HOUR = 17

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

if not OPENROUTER_API_KEY:
    raise ValueError("Missing OPENROUTER_API_KEY in .env file!")