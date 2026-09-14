import os
import io
import feedparser
import requests
from pydantic import BaseModel
from src.config import config
from src.drive_sync import load_manifest

class PodcastEpisode(BaseModel):
    podcast_name: str
    episode_id: str
    title: str
    summary: str
    audio_url: str
    published: str

PODCAST_FEEDS = {
    "Pharmacist Ben's Bytes": config.RSS_BENS_BYTES,
    "The Mineral Way": config.RSS_MINERAL_WAY,
    "The Art of Aging Well": config.RSS_AGING_WELL,
}

def fetch_unprocessed_podcast_episodes(max_per_feed: int = 1) -> list[PodcastEpisode]:
    """
    Fetches the latest unprocessed episodes from the 3 podcast RSS feeds.
    """
    manifest = load_manifest()
    processed_episodes = set(manifest.get("podcast_episodes", []))
    new_episodes: list[PodcastEpisode] = []

    for show_name, feed_url in PODCAST_FEEDS.items():
        if not feed_url or "placeholder" in feed_url:
            continue
        try:
            feed = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries:
                ep_id = entry.get("id") or entry.get("link") or entry.get("title")
                if not ep_id or ep_id in processed_episodes:
                    continue

                # Locate audio enclosure URL
                audio_url = None
                for enc in entry.get("enclosures", []):
                    if "audio" in enc.get("type", "") or enc.get("href", "").endswith((".mp3", ".m4a")):
                        audio_url = enc.get("href")
                        break
                
                if not audio_url:
                    # Check links
                    for link in entry.get("links", []):
                        if "audio" in link.get("type", "") or link.get("href", "").endswith((".mp3", ".m4a")):
                            audio_url = link.get("href")
                            break

                if audio_url:
                    new_episodes.append(PodcastEpisode(
                        podcast_name=show_name,
                        episode_id=ep_id,
                        title=entry.get("title", "Untitled Episode"),
                        summary=entry.get("summary", "")[:300],
                        audio_url=audio_url,
                        published=entry.get("published", "")
                    ))
                    count += 1
                    if count >= max_per_feed:
                        break
        except Exception as e:
            print(f"Error parsing feed for '{show_name}' ({feed_url}): {e}")

    return new_episodes

def download_podcast_audio_sample(audio_url: str, output_path: str, max_bytes: int = 15 * 1024 * 1024):
    """
    Downloads the first few minutes (up to ~15MB) of an audio stream for quick processing.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    headers = {"User-Agent": "PharmacistBenPromoEngine/1.0"}
    with requests.get(audio_url, headers=headers, stream=True, timeout=30) as r:
        r.raise_for_status()
        downloaded = 0
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded >= max_bytes:
                    break
