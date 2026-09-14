import os
import json
import subprocess
import requests
from src.config import config

BUFFER_API_BASE = "https://api.bufferapp.com/1"

def get_buffer_profiles() -> list[dict]:
    """
    Fetches connected social profiles and service types.
    Tries modern Buffer CLI first, then falls back to REST API.
    """
    token = config.BUFFER_ACCESS_TOKEN
    if not token:
        return []

    # 1. Try Buffer CLI
    try:
        env = os.environ.copy()
        env["BUFFER_API_KEY"] = token
        cmd = ["npx", "--yes", "@bufferapp/cli", "channels", "list", "--output", "json"]
        res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            channels = json.loads(res.stdout)
            if isinstance(channels, list):
                return [{"id": c.get("id"), "service": c.get("service"), "formatted_username": c.get("name")} for c in channels]
    except Exception:
        pass

    # 2. Fallback to REST API
    url = f"{BUFFER_API_BASE}/profiles.json"
    params = {"access_token": token}
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Buffer profiles: {e}")
        return []

def get_channel_queue_count(profile_id: str) -> int:
    """Returns number of pending scheduled posts in the channel queue."""
    token = config.BUFFER_ACCESS_TOKEN
    if not token:
        return 0
    url = f"{BUFFER_API_BASE}/profiles/{profile_id}/updates/pending.json"
    params = {"access_token": token}
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("total", 0)
    except Exception as e:
        return 0

def can_schedule(profile_id: str, limit: int = 10) -> bool:
    """Checks if the profile has free queue slots under the Free plan cap (10 posts)."""
    count = get_channel_queue_count(profile_id)
    return count < limit

def schedule_via_buffer_cli(channel_id: str, text: str, media_url: str | None = None) -> dict | None:
    """Uses the modern Buffer CLI (@bufferapp/cli) to create a post."""
    token = config.BUFFER_ACCESS_TOKEN
    if not token:
        return None
    env = os.environ.copy()
    env["BUFFER_API_KEY"] = token
    
    post_input = {
        "channelId": channel_id,
        "schedulingType": "automatic",
        "mode": "addToQueue",
        "text": text
    }
    if media_url:
        post_input["assets"] = [{"video": {"url": media_url}}]

    cmd = ["npx", "--yes", "@bufferapp/cli", "posts", "create", "--json", json.dumps(post_input), "--output", "json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
        if res.returncode == 0 and res.stdout.strip():
            return json.loads(res.stdout)
    except Exception as e:
        print(f"Buffer CLI scheduling attempt notice: {e}")
    return None

def schedule_buffer_post(
    profile_ids: list[str],
    text: str,
    media_url: str | None = None
) -> dict:
    """
    Schedules an update to one or more Buffer profiles.
    Tries Buffer CLI first, then falls back to REST API.
    """
    if not config.BUFFER_ACCESS_TOKEN:
        print(f"[Dry Run / Mock] Buffer update for profiles {profile_ids}: {text[:60]}... (media: {media_url})")
        return {"success": True, "mock": True, "updates": [{"id": "mock_update_123"}]}

    # Try modern Buffer CLI for the first profile
    if profile_ids:
        cli_result = schedule_via_buffer_cli(profile_ids[0], text, media_url)
        if cli_result:
            return {"success": True, "cli": True, "updates": [{"id": cli_result.get("id", "cli_post")]}}

    # Fallback to REST API
    url = f"{BUFFER_API_BASE}/updates/create.json"
    params = {"access_token": config.BUFFER_ACCESS_TOKEN}
    
    payload = {
        "text": text,
        "now": False,
        "top": False
    }
    for idx, pid in enumerate(profile_ids):
        payload[f"profile_ids[{idx}]"] = pid
    if media_url:
        payload["media[video]"] = media_url

    response = requests.post(url, params=params, data=payload, timeout=20)
    response.raise_for_status()
    return response.json()

def dispatch_platform_post(
    profile_id: str,
    platform_hint: str,
    caption_tiktok: str,
    caption_instagram: str,
    post_x: str,
    media_url: str | None = None
) -> dict:
    """
    Selects the right copy for the specific platform type and dispatches to Buffer.
    """
    platform = platform_hint.lower()
    if "tiktok" in platform:
        copy_text = caption_tiktok
    elif "instagram" in platform or "insta" in platform:
        copy_text = caption_instagram
    elif "x" in platform or "twitter" in platform:
        copy_text = post_x
    else:
        copy_text = caption_instagram  # Default balanced fallback

    return schedule_buffer_post([profile_id], text=copy_text, media_url=media_url)
