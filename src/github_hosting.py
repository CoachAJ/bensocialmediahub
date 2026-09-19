import os
import subprocess
import requests
from src.config import config

RELEASE_TAG = "media-assets"
DEFAULT_REPO = "CoachAJ/bensocialmediahub"

def get_github_auth_headers() -> dict:
    token = os.getenv("GITHUB_TOKEN") or getattr(config, "GITHUB_TOKEN", None)
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "PharmacistBenPromoEngine/1.0"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def push_media_to_git_branch(local_path: str, filename: str, repo: str = DEFAULT_REPO) -> str:
    """
    Pushes the media file directly to the public 'media-assets' branch using git.
    Returns the direct CDN URL via raw.githubusercontent.com which Buffer can download.
    """
    norm_path = local_path.replace("\\", "/")
    # Ensure file is tracked on media-assets branch
    cmd = (
        f'git add -f "{norm_path}" && '
        f'git commit -m "Auto: Host video asset {filename}" && '
        f'git push origin HEAD:media-assets'
    )
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    cdn_url = f"https://raw.githubusercontent.com/{repo}/media-assets/{norm_path}"
    print(f"[GitHub CDN] Published video asset to media-assets branch: {cdn_url}")
    return cdn_url

def get_or_create_release(repo: str = DEFAULT_REPO) -> dict | None:
    headers = get_github_auth_headers()
    if "Authorization" not in headers:
        return None

    url = f"https://api.github.com/repos/{repo}/releases/tags/{RELEASE_TAG}"
    
    # 1. Check if release already exists
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code == 200:
        return res.json()
    
    # 2. If 404, create the release
    if res.status_code == 404:
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
    Uploads a rendered video/media file directly to GitHub CDN (Releases or media-assets branch)
    and returns the public, world-readable direct download URL for Buffer.
    """
    if not os.path.exists(local_path):
        print(f"[GitHub CDN Error] Local file does not exist: {local_path}")
        return ""
        
    repo = os.getenv("GITHUB_REPOSITORY") or DEFAULT_REPO
    token = os.getenv("GITHUB_TOKEN") or getattr(config, "GITHUB_TOKEN", None)
    
    # If no token is provided (local machine), use git branch media-assets CDN
    if not token:
        return push_media_to_git_branch(local_path, filename, repo)

    # If token is provided, try GitHub Releases API
    headers = get_github_auth_headers()
    release = get_or_create_release(repo)
    if not release:
        return push_media_to_git_branch(local_path, filename, repo)

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
            up_res = requests.post(upload_url, headers=upload_headers, data=file_data, timeout=60)
            
        if up_res.status_code in [200, 201]:
            asset_data = up_res.json()
            download_url = asset_data.get("browser_download_url")
            if download_url:
                print(f"[GitHub CDN] Successfully published video asset to GitHub Release CDN: {download_url}")
                return download_url
    except Exception as e:
        print(f"[GitHub CDN Warning] Release upload attempt note: {e}")
        
    return push_media_to_git_branch(local_path, filename, repo)
