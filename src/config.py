import os
import json
import base64
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Config(BaseModel):
    # API Credentials
    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    BUFFER_ACCESS_TOKEN: str = Field(default_factory=lambda: os.getenv("BUFFER_ACCESS_TOKEN", ""))
    BUFFER_PROFILE_IDS: list[str] = Field(
        default_factory=lambda: [
            p.strip() for p in os.getenv("BUFFER_PROFILE_IDS", "").split(",") if p.strip()
        ]
    )
    # Profile mapping allows mapping specific Buffer Profile IDs to their platform type (e.g. {"id1": "tiktok", "id2": "instagram", "id3": "x"})
    BUFFER_PROFILE_MAP_JSON: str = Field(default_factory=lambda: os.getenv("BUFFER_PROFILE_MAP_JSON", "{}"))

    # Google Drive & Sheets Credentials
    GDRIVE_SERVICE_ACCOUNT_JSON: str = Field(default_factory=lambda: os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON", ""))
    GDRIVE_EXISTING_FOLDER_ID: str = Field(default_factory=lambda: os.getenv("GDRIVE_EXISTING_FOLDER_ID", ""))
    GDRIVE_RAW_FOLDER_ID: str = Field(default_factory=lambda: os.getenv("GDRIVE_RAW_FOLDER_ID", ""))
    GDRIVE_OUTPUT_FOLDER_ID: str = Field(default_factory=lambda: os.getenv("GDRIVE_OUTPUT_FOLDER_ID", ""))
    GOOGLE_SHEET_ID: str = Field(default_factory=lambda: os.getenv("GOOGLE_SHEET_ID", ""))

    # Podcast RSS Feeds
    RSS_BENS_BYTES: str = Field(
        default_factory=lambda: os.getenv("RSS_BENS_BYTES", "https://anchor.fm/s/placeholder/podcast/rss")
    )
    RSS_MINERAL_WAY: str = Field(
        default_factory=lambda: os.getenv("RSS_MINERAL_WAY", "https://mineralway.libsyn.com/rss")
    )
    RSS_AGING_WELL: str = Field(
        default_factory=lambda: os.getenv("RSS_AGING_WELL", "https://feeds.buzzsprout.com/placeholder.rss")
    )

    # Core Destinations
    WEBSITE_URL: str = Field(default="https://pharmacistbensacademy.com")
    PODCASTS_URL: str = Field(default="https://pharmacistbensacademy.com/podcasts")
    MANIFEST_PATH: str = Field(default="data/processed.json")

    def get_gdrive_credentials_dict(self) -> dict:
        encoded_or_raw = self.GDRIVE_SERVICE_ACCOUNT_JSON.strip()
        if not encoded_or_raw:
            raise ValueError("GDRIVE_SERVICE_ACCOUNT_JSON is missing or empty.")
        
        # Check if it's already a valid JSON string
        try:
            return json.loads(encoded_or_raw)
        except json.JSONDecodeError:
            pass

        # Check if it's a file path pointing to service-account.json
        if os.path.isfile(encoded_or_raw):
            with open(encoded_or_raw, "r", encoding="utf-8") as f:
                return json.load(f)

        # Attempt base64 decode
        try:
            decoded = base64.b64decode(encoded_or_raw).decode("utf-8")
            return json.loads(decoded)
        except Exception as e:
            raise ValueError(f"Failed to parse GDRIVE_SERVICE_ACCOUNT_JSON as JSON, file path, or base64: {e}")

    def get_profile_mapping(self) -> dict[str, str]:
        """Returns dict of profile_id -> platform ('tiktok', 'instagram', 'x')"""
        try:
            return json.loads(self.BUFFER_PROFILE_MAP_JSON)
        except Exception:
            return {}

config = Config()
