import os
import requests
from google import genai
from src.config import config

def generate_gemini_image(prompt: str, output_path: str) -> str | None:
    """
    Attempts to generate an image via Gemini multimodal models (e.g. gemini-3.1-flash-image).
    Works automatically when the API key has image generation quota / billing enabled.
    """
    if not config.GEMINI_API_KEY or not prompt:
        return None
    try:
        # Use short timeout so quota limit 0 on free tier fails immediately to fallback
        client = genai.Client(api_key=config.GEMINI_API_KEY, http_options=dict(timeout=6000))
        for model_name in ["gemini-3.1-flash-image", "gemini-2.5-flash-image"]:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=f"Realistic 3D biomedical scientific illustration, highly detailed, dark studio background: {prompt}"
                )
                if resp.candidates and resp.candidates[0].content:
                    for part in resp.candidates[0].content.parts:
                        if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            with open(output_path, "wb") as f:
                                f.write(part.inline_data.data)
                            return output_path
            except Exception:
                # If model is unavailable or quota limit 0, break fast to fallback
                break
    except Exception as e:
        print(f"Gemini image generation notice: {e}")
    return None

def fetch_wikimedia_scientific_image(query: str, output_path: str) -> str | None:
    """
    Fetches a high-resolution, relevant biomedical or scientific illustration from
    open scientific archives matching the topic keywords.
    """
    if not query:
        return None
    try:
        url = "https://en.wikipedia.org/w/api.php"
        clean_query = query.replace(",", " ").strip()
        params = {
            "action": "query",
            "format": "json",
            "prop": "pageimages",
            "generator": "search",
            "gsrsearch": clean_query,
            "gsrlimit": 4,
            "pithumbsize": 1280
        }
        headers = {"User-Agent": "PharmacistBenPromoEngine/1.0 (contact@pharmacistbensacademy.com)"}
        resp = requests.get(url, params=params, headers=headers, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for p in pages.values():
                thumb = p.get("thumbnail", {}).get("source")
                if thumb and thumb.startswith("http"):
                    img_resp = requests.get(thumb, headers=headers, timeout=15)
                    if img_resp.status_code == 200 and len(img_resp.content) > 10000:
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(img_resp.content)
                        return output_path
    except Exception as e:
        print(f"Scientific image search notice for '{query}': {e}")
    return None

def generate_clip_topic_image(
    prompt: str,
    keywords: str,
    output_path: str,
    fallback_image: str | None = None
) -> str | None:
    """
    Generates or retrieves a topic-relevant biological illustration for an audio short.
    Tries Gemini image generation first, falls back to open scientific illustration repositories,
    and finally falls back to the show/host brand artwork if offline.
    """
    # 1. Attempt native Gemini AI image generation
    if prompt:
        img_path = generate_gemini_image(prompt, output_path)
        if img_path and os.path.exists(img_path) and os.path.getsize(img_path) > 1000:
            return img_path

    # 2. Attempt topic keyword scientific illustration search
    search_terms = keywords or prompt[:80]
    if search_terms:
        img_path = fetch_wikimedia_scientific_image(search_terms, output_path)
        if img_path and os.path.exists(img_path) and os.path.getsize(img_path) > 1000:
            return img_path

    # 3. Graceful fallback to show/brand portrait
    if fallback_image and os.path.exists(fallback_image):
        return fallback_image

    return None
