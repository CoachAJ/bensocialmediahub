import os
import sys
import json
import shutil
import subprocess
import requests
from src.config import config

BUFFER_API_BASE = "https://api.bufferapp.com/1"

def run_buffer_cli(subcommand: list[str], input_str: str | None = None, timeout: int = 30) -> tuple[int, str, str]:
    """
    Executes a Buffer CLI subcommand with robust cross-platform compatibility.
    Handles Linux/POSIX (shell=False) vs Windows (.cmd batch wrappers).
    """
    token = config.BUFFER_ACCESS_TOKEN
    env = os.environ.copy()
    if token:
        env["BUFFER_API_KEY"] = token
        env["BUFFER_ACCESS_TOKEN"] = token

    # Check if 'buffer' CLI is installed globally or in PATH
    buffer_bin = shutil.which("buffer")
    if buffer_bin:
        cmd = [buffer_bin] + subcommand
    else:
        npx_bin = shutil.which("npx") or "npx"
        cmd = [npx_bin, "--yes", "@bufferapp/cli"] + subcommand

    is_win = sys.platform.startswith("win")
    try:
        if is_win:
            res = subprocess.run(cmd, input=input_str, capture_output=True, text=True, env=env, timeout=timeout, shell=True)
        else:
            # On Linux/macOS, shell=False prevents /bin/sh -c argument truncation
            res = subprocess.run(cmd, input=input_str, capture_output=True, text=True, env=env, timeout=timeout, shell=False)
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        return 1, "", str(e)

def get_buffer_profiles() -> list[dict]:
    """
    Fetches connected social profiles and service types.
    Tries modern Buffer CLI first, then falls back to REST API.
    """
    token = config.BUFFER_ACCESS_TOKEN
    if not token:
        return []

    # 1. Try Buffer CLI
    retcode, stdout, stderr = run_buffer_cli(["channels", "list", "--output", "json"], timeout=15)
    if retcode == 0 and stdout.strip():
        try:
            channels = json.loads(stdout)
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

    # 1. Try Buffer CLI with organization ID if available
    org_id = config.BUFFER_ORGANIZATION_ID
    if org_id:
        retcode, stdout, stderr = run_buffer_cli([
            "posts", "list", "--organization-id", org_id,
            "--fields", "items.id,items.channel.id,items.status", "--output", "json"
        ], timeout=15)
        if retcode == 0 and stdout.strip():
            try:
                data = json.loads(stdout)
                items = data.get("items", [])
                channel_posts = [p for p in items if (p.get("channel", {}).get("id") == profile_id or p.get("channelId") == profile_id) and p.get("status") in ["scheduled", "sending"]]
                return len(channel_posts)
            except Exception:
                pass

    # 2. Fallback to legacy REST API
    url = f"{BUFFER_API_BASE}/profiles/{profile_id}/updates/pending.json"
    params = {"access_token": token}
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("total", 0)
    except Exception:
        return 0

def can_schedule(profile_id: str, limit: int = 10) -> bool:
    """Checks if the profile has free queue slots under the Free plan cap (10 posts)."""
    count = get_channel_queue_count(profile_id)
    return count < limit

def schedule_via_buffer_cli(channel_id: str, text: str, media_url: str | None = None, platform_hint: str = "social") -> dict | None:
    """Uses the modern Buffer CLI (@bufferapp/cli) to create a post."""
    token = config.BUFFER_ACCESS_TOKEN
    if not token:
        return None
    
    post_input = {
        "channelId": channel_id,
        "schedulingType": "automatic",
        "mode": "addToQueue",
        "text": text
    }
    
    # Attach video asset if available
    if media_url:
        post_input["assets"] = [{"video": {"url": media_url}}]

    plat = platform_hint.lower()
    if "instagram" in plat:
        post_input["metadata"] = {
            "instagram": {
                "type": "reel",
                "shouldShareToFeed": True
            }
        }
    elif "tiktok" in plat:
        post_input["metadata"] = {
            "tiktok": {
                "isAiGenerated": False
            }
        }

    retcode, stdout, stderr = run_buffer_cli(["posts", "create", "--input", "-", "--output", "json"], input_str=json.dumps(post_input), timeout=30)
    if retcode == 0 and stdout.strip():
        try:
            raw = json.loads(stdout)
            return raw.get("post", raw)
        except Exception:
            pass
    else:
        notice = stderr.strip() or stdout.strip()
        print(f"[Buffer CLI Notice] Direct queue attempt: {notice}")
        # If automatic queue rejected, fallback to saving as draft
        draft_input = dict(post_input)
        draft_input["saveToDraft"] = True
        d_ret, d_stdout, d_stderr = run_buffer_cli(["posts", "create", "--input", "-", "--output", "json"], input_str=json.dumps(draft_input), timeout=30)
        if d_ret == 0 and d_stdout.strip():
            try:
                raw_draft = json.loads(d_stdout)
                post_data = raw_draft.get("post", raw_draft)
                print(f"[Buffer CLI] Saved post to drafts for channel {channel_id} (ID: {post_data.get('id')})")
                return post_data
            except Exception:
                pass
    return None

def schedule_buffer_post(
    profile_ids: list[str],
    text: str,
    media_url: str | None = None,
    platform_hint: str = "social"
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
        cli_result = schedule_via_buffer_cli(profile_ids[0], text, media_url, platform_hint=platform_hint)
        if cli_result and cli_result.get("id"):
            return {"success": True, "cli": True, "updates": [{"id": cli_result.get("id")}]}

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

    try:
        response = requests.post(url, params=params, data=payload, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Notice: Buffer REST API update note: {e}")
        return {"success": False, "updates": [{"id": "pending_manual"}]}

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

    return schedule_buffer_post([profile_id], text=copy_text, media_url=media_url, platform_hint=platform_hint)
