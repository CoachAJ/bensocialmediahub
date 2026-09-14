import requests
from src.config import config

BUFFER_API_BASE = "https://api.bufferapp.com/1"

def get_buffer_profiles() -> list[dict]:
    """Fetches connected social profiles and their service types from Buffer."""
    if not config.BUFFER_ACCESS_TOKEN:
        return []
    url = f"{BUFFER_API_BASE}/profiles.json"
    params = {"access_token": config.BUFFER_ACCESS_TOKEN}
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Buffer profiles: {e}")
        return []

def get_channel_queue_count(profile_id: str) -> int:
    """Returns number of pending scheduled posts in the channel queue."""
    if not config.BUFFER_ACCESS_TOKEN:
        return 0
    url = f"{BUFFER_API_BASE}/profiles/{profile_id}/updates/pending.json"
    params = {"access_token": config.BUFFER_ACCESS_TOKEN}
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("total", 0)
    except Exception as e:
        print(f"Error querying pending updates for profile {profile_id}: {e}")
        return 0

def can_schedule(profile_id: str, limit: int = 10) -> bool:
    """Checks if the profile has free queue slots under the Free plan cap (10 posts)."""
    count = get_channel_queue_count(profile_id)
    return count < limit

def schedule_buffer_post(
    profile_ids: list[str],
    text: str,
    media_url: str | None = None
) -> dict:
    """
    Schedules an update to one or more Buffer profiles.
    Attaches video media if media_url is provided.
    """
    if not config.BUFFER_ACCESS_TOKEN:
        print(f"[Dry Run / Mock] Buffer update for profiles {profile_ids}: {text[:60]}... (media: {media_url})")
        return {"success": True, "mock": True, "updates": [{"id": "mock_update_123"}]}

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
