import os
import sys
import subprocess
import requests
from src.config import config

RELEASE_TAG = "media-assets"
DEFAULT_REPO = "CoachAJ/bensocialmediahub"

def get_github_auth_headers() -> dict:
    token = os.getenv("GITHUB_TOKEN") or getattr(config, "GITHUB_TOKEN", None)
    if not token:
        # Auto-discover token from local Git Credential Manager
        try:
            cmd = "echo protocol=https`nhost=github.com | git credential fill" if sys.platform.startswith("win") else "printf 'protocol=https\\nhost=github.com\\n' | git credential fill"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            for line in res.stdout.splitlines():
                if line.startswith("password="):
                    token = line.split("=", 1)[1].strip()
                    break
        except Exception:
            pass

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "PharmacistBenPromoEngine/1.0"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def get_or_create_release(repo: str = DEFAULT_REPO) -> dict | None:
    headers = get_github_auth_headers()
    url = f"https://api.github.com/repos/{repo}/releases/tags/{RELEASE_TAG}"
    
    # 1. Check if release already exists
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code == 200:
        return res.json()
    
    # 2. If 404, create the release (requires authorization)
    if res.status_code == 404 and "Authorization" in headers:
        create_url = f"https://api.github.com/repos/{repo}/releases"
        payload = {
            "tag_name": RELEASE_TAG,
            "target_commitish": "main",
            "name": "Social Media Video Assets CDN",
            "body": "Automated asset hosting for Buffer social media distribution (audiograms and branded shorts).",
            "draft": False,
            "prerelease": False
        }
        create_res = requests.post(create_url, headers=headers, json=payload, timeout=20)
        if create_res.status_code in [200, 201]:
            return create_res.json()
        print(f"[GitHub CDN Warning] Could not create release '{RELEASE_TAG}': {create_res.status_code} - {create_res.text}")
        
    return None

def upload_to_github_release(local_path: str, filename: str) -> str:
    """
    Uploads a rendered video/media file directly to the GitHub Release CDN
    and returns the public, world-readable direct download URL for Buffer.
    """
    if not os.path.exists(local_path):
        print(f"[GitHub CDN Error] Local file does not exist: {local_path}")
        return ""
        
    repo = os.getenv("GITHUB_REPOSITORY") or DEFAULT_REPO
    headers = get_github_auth_headers()
    public_cdn_url = f"https://github.com/{repo}/releases/download/{RELEASE_TAG}/{filename}"
    
    release = get_or_create_release(repo)
    if not release:
        print(f"[GitHub CDN Notice] Release not accessible directly, fallback URL: {public_cdn_url}")
        return public_cdn_url

    release_id = release.get("id")
    upload_url_template = release.get("upload_url", "")
    base_upload_url = upload_url_template.split("{")[0] if "{" in upload_url_template else f"https://uploads.github.com/repos/{repo}/releases/{release_id}/assets"
    
    # Delete existing asset with same name if present so we can overwrite
    existing_assets = release.get("assets", [])
    for asset in existing_assets:
        if asset.get("name") == filename:
            asset_id = asset.get("id")
            del_url = f"https://api.github.com/repos/{repo}/releases/assets/{asset_id}"
            try:
                requests.delete(del_url, headers=headers, timeout=15)
            except Exception:
                pass

    # Upload the binary asset
    upload_url = f"{base_upload_url}?name={filename}"
    upload_headers = dict(headers)
    upload_headers["Content-Type"] = "video/mp4" if filename.lower().endswith(".mp4") else "application/octet-stream"
    
    try:
        with open(local_path, "rb") as f:
            file_data = f.read()
            upload_headers["Content-Length"] = str(len(file_data))
            up_res = requests.post(upload_url, headers=upload_headers, data=file_data, timeout=90)
            
        if up_res.status_code in [200, 201]:
            asset_data = up_res.json()
            download_url = asset_data.get("browser_download_url") or public_cdn_url
            print(f"[GitHub CDN] Successfully published video asset to GitHub Release CDN: {download_url}")
            return download_url
        else:
            print(f"[GitHub CDN Warning] Release upload response {up_res.status_code}: {up_res.text[:200]}")
            return public_cdn_url
    except Exception as e:
        print(f"[GitHub CDN Error] Release upload failed: {e}")
        return public_cdn_url
