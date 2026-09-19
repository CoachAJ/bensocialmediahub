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

    # 4. Check for Google Cloud CLI Application Default Credentials (ADC)
    try:
        import google.auth
        creds, _ = google.auth.default(scopes=SCOPES)
        return creds
    except Exception:
        pass

    raise ValueError("No Google credentials found. Provide GDRIVE_SERVICE_ACCOUNT_JSON in .env or run 'gcloud auth application-default login'.")

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

from src.github_hosting import upload_to_github_release

def fetch_unprocessed_files(folder_id: str, manifest_key: str) -> list[dict]:
    manifest = load_manifest()
    processed_ids = set(manifest.get(manifest_key, []))
    items = []

    # 1. Discover local input shorts first (Zero-Google Drive direct upload folder)
    input_dirs = ["input_shorts", "tmp/raw_shorts", "tmp/shared_drive", "tmp/test_download"]
    for search_dir in input_dirs:
        if os.path.exists(search_dir):
            for f in os.listdir(search_dir):
                if f.lower().endswith((".mp4", ".mov", ".m4v", ".webm")):
                    file_path = os.path.join(search_dir, f)
                    if not any(it["name"] == f for it in items):
                        items.append({
                            "id": f,
                            "name": f,
                            "direct_url": "", # Will be uploaded to GitHub Releases CDN when rendered
                            "local_path": file_path
                        })

    # 2. Check remote Google Drive folder if configured and needed
    if folder_id:
        if config.GDRIVE_SERVICE_ACCOUNT_JSON:
            try:
                service = get_drive_service()
                query = f"'{folder_id}' in parents and trashed = false"
                results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
                drive_files = results.get("files", [])
                for df in drive_files:
                    if not any(it["id"] == df["id"] or it["name"] == df["name"] for it in items):
                        items.append({
                            "id": df["id"],
                            "name": df["name"],
                            "direct_url": f"https://drive.google.com/uc?export=download&id={df['id']}",
                            "local_path": None
                        })
            except Exception as e:
                print(f"[Drive Sync] Service account note: {e}")
        else:
            # Public shared Drive folder sync
            try:
                import gdown
                folder_url = f"https://drive.google.com/drive/folders/{folder_id}?usp=sharing"
                remote_files = gdown.download_folder(url=folder_url, skip_download=True, quiet=True)
                if remote_files:
                    for rf in remote_files:
                        fname = os.path.basename(rf.path)
                        if fname.lower().endswith((".mp4", ".mov", ".m4v", ".webm")):
                            real_id = rf.id
                            if not any(it["id"] == real_id or it["name"] == fname for it in items):
                                items.append({
                                    "id": real_id,
                                    "name": fname,
                                    "direct_url": f"https://drive.google.com/uc?export=download&id={real_id}",
                                    "local_path": None
                                })
            except Exception as e:
                print(f"[Drive Sync] Public Drive sync note: {e}")

    unprocessed = [item for item in items if item["id"] not in processed_ids and item["name"] not in processed_ids]
    return unprocessed

def download_file(file_id: str, output_path: str, item_meta: dict | None = None):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if item_meta and item_meta.get("local_path") and os.path.exists(item_meta["local_path"]):
        import shutil
        if os.path.abspath(item_meta["local_path"]) != os.path.abspath(output_path):
            shutil.copy2(item_meta["local_path"], output_path)
        return

    try:
        service = get_drive_service()
        request = service.files().get_media(fileId=file_id)
        with io.FileIO(output_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
    except Exception:
        import gdown
        gdown.download(id=file_id, output=output_path, quiet=True)

def upload_public_clip(local_path: str, filename: str, folder_id: str | None = None) -> str:
    """
    Uploads a processed short or audiogram to the GitHub Releases CDN,
    returning a direct public download URL for Buffer.
    Keeps Google Drive 100% clean and free of generated clips.
    """
    return upload_to_github_release(local_path, filename)
