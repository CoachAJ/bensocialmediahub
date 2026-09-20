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
    image_url: str | None = None

def get_podcast_feeds() -> dict[str, str]:
    return {
        "Pharmacist Ben's Bytes": config.RSS_BENS_BYTES,
        "The Mineral Way": config.RSS_MINERAL_WAY,
        "The Art of Aging Well": config.RSS_AGING_WELL,
    }

def fetch_unprocessed_podcast_episodes(max_per_feed: int = 1) -> list[PodcastEpisode]:
    """
    Fetches the latest unprocessed episodes from the 3 podcast RSS feeds.
    Extracts show/episode artwork URLs alongside the audio streams.
    """
    manifest = load_manifest()
    processed_episodes = set(manifest.get("podcast_episodes", []))
    new_episodes: list[PodcastEpisode] = []
    feeds = get_podcast_feeds()

    for show_name, feed_url in feeds.items():
        if not feed_url or "placeholder" in feed_url:
            continue
        try:
            feed = feedparser.parse(feed_url)
            count = 0
            
            # Extract channel/show-level cover art URL
            show_image_url = None
            feed_img = feed.feed.get("image", {})
            if isinstance(feed_img, dict):
                show_image_url = feed_img.get("href")
            elif isinstance(feed_img, str) and feed_img.startswith("http"):
                show_image_url = feed_img

            if not show_image_url and feed.feed.get("itunes_image"):
                itunes_img = feed.feed.get("itunes_image")
                if isinstance(itunes_img, dict):
                    show_image_url = itunes_img.get("href")
                elif isinstance(itunes_img, str) and itunes_img.startswith("http"):
                    show_image_url = itunes_img

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

                # Extract episode-specific artwork or fallback to show-level artwork
                ep_image_url = None
                if entry.get("image"):
                    img_data = entry.get("image")
                    if isinstance(img_data, dict):
                        ep_image_url = img_data.get("href")
                    elif isinstance(img_data, str) and img_data.startswith("http"):
                        ep_image_url = img_data
                if not ep_image_url and entry.get("itunes_image"):
                    itunes_img = entry.get("itunes_image")
                    if isinstance(itunes_img, dict):
                        ep_image_url = itunes_img.get("href")
                    elif isinstance(itunes_img, str) and itunes_img.startswith("http"):
                        ep_image_url = itunes_img

                final_image_url = ep_image_url or show_image_url

                if audio_url:
                    new_episodes.append(PodcastEpisode(
                        podcast_name=show_name,
                        episode_id=ep_id,
                        title=entry.get("title", "Untitled Episode"),
                        summary=entry.get("summary", "")[:300],
                        audio_url=audio_url,
                        published=entry.get("published", ""),
                        image_url=final_image_url
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

def download_podcast_image(image_url: str, output_path: str) -> str | None:
    """
    Downloads podcast episode or show cover art, caching it locally for video compositing.
    """
    if not image_url:
        return None
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(image_url, headers=headers, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 500:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return output_path
    except Exception as e:
        print(f"Warning: Could not download image {image_url}: {e}")
    return None
