import os
import io
import json
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from src.config import config

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

def get_credentials():
    """
    Returns valid Google credentials:
    1. Checks for Service Account JSON in config.
    2. Falls back to OAuth 2.0 user credentials (token.json or client_secret.json).
    """
    token_path = "token.json"
    client_secrets_path = "client_secret.json"

    # 1. Try Service Account JSON first
    if config.GDRIVE_SERVICE_ACCOUNT_JSON:
        try:
            creds_dict = config.get_gdrive_credentials_dict()
            return ServiceAccountCredentials.from_service_account_info(creds_dict, scopes=SCOPES)
        except Exception as e:
            print(f"Service account parsing note: {e}")

    # 2. Check for existing OAuth2 user token
    if os.path.exists(token_path):
        try:
            return UserCredentials.from_authorized_user_file(token_path, SCOPES)
        except Exception:
            pass

    # 3. Check for OAuth2 client_secret.json desktop app
    if os.path.exists(client_secrets_path):
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        return creds

    raise ValueError("No Google credentials found. Provide GDRIVE_SERVICE_ACCOUNT_JSON in .env or place client_secret.json in project root.")

def get_drive_service():
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)

def load_manifest() -> dict:
    if os.path.exists(config.MANIFEST_PATH):
        with open(config.MANIFEST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure required keys exist
            if "existing_shorts" not in data:
                data["existing_shorts"] = []
            if "raw_media" not in data:
                data["raw_media"] = []
            if "podcast_episodes" not in data:
                data["podcast_episodes"] = []
            return data
    return {"existing_shorts": [], "raw_media": [], "podcast_episodes": []}

def save_manifest(manifest: dict):
    os.makedirs(os.path.dirname(config.MANIFEST_PATH), exist_ok=True)
    with open(config.MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def fetch_unprocessed_files(folder_id: str, manifest_key: str) -> list[dict]:
    if not folder_id:
        return []
    service = get_drive_service()
    manifest = load_manifest()
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    items = results.get("files", [])
    
    processed_ids = set(manifest.get(manifest_key, []))
    unprocessed = [item for item in items if item["id"] not in processed_ids]
    return unprocessed

def download_file(file_id: str, output_path: str):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with io.FileIO(output_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

def upload_public_clip(local_path: str, filename: str, folder_id: str | None = None) -> str:
    """
    Uploads a processed short/audiogram to Google Drive, sets public read permission,
    and returns a direct stream/download URL for Buffer API.
    """
    service = get_drive_service()
    target_folder = folder_id or config.GDRIVE_OUTPUT_FOLDER_ID or config.GDRIVE_EXISTING_FOLDER_ID
    
    file_metadata = {"name": filename}
    if target_folder:
        file_metadata["parents"] = [target_folder]
        
    mime_type = "video/mp4" if filename.lower().endswith(".mp4") else "image/gif"
    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
    
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webContentLink, webViewLink"
    ).execute()
    
    file_id = uploaded_file.get("id")
    
    # Make the file publicly accessible so Buffer can fetch the video stream
    try:
        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"}
        ).execute()
    except Exception as e:
        print(f"Warning: could not set public permission on Drive file {file_id}: {e}")
        
    # Direct download link for Buffer
    direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    return direct_url
