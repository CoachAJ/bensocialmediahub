import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from src.config import config

def get_gemini_client():
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    return genai.Client(api_key=config.GEMINI_API_KEY)

class ClipProposal(BaseModel):
    start_time: str = Field(description="Format HH:MM:SS or MM:SS")
    end_time: str = Field(description="Format HH:MM:SS or MM:SS")
    hook_headline: str = Field(description="Short, punchy upper video hook (under 7 words)")
    burned_cta_text: str = Field(description="Lower-third CTA text, e.g., 'Full Episode @ PharmacistBensAcademy.com'")
    caption_tiktok: str = Field(description="Punchy TikTok caption with relevant hashtags and link-in-bio prompt")
    caption_instagram: str = Field(description="Educational Instagram caption with biological value, hashtags, and link-in-bio prompt")
    post_x: str = Field(description="Concise X/Twitter post under 250 characters including direct link to pharmacistbensacademy.com/podcasts")

class LongFormAnalysis(BaseModel):
    episode_core_concept: str
    quiz_question: str
    quiz_options: list[str]
    quiz_correct_index: int
    quiz_explanation: str
    clips: list[ClipProposal]

class ExistingShortCaptions(BaseModel):
    hook_headline: str = Field(description="Punchy upper video hook (max 6 words)")
    burned_cta_text: str = Field(description="Visual lower-third banner text (e.g. 'More on PharmacistBensAcademy.com')")
    caption_tiktok: str
    caption_instagram: str
    post_x: str

SYSTEM_EDITORIAL_RULES = f"""
You are the senior editorial director and digital growth strategist for Pharmacist Ben's holistic health broadcasts and academy.

Core Scientific & Philosophical Guidelines:
1. Emphasize health as a holistic biological process, cellular energy, and the 90 essential nutrients.
2. Address root causes (metabolism, digestive integrity, blood purification, mineral balance) rather than symptom chasing.
3. NEVER make "health in a bottle", miracle cure, or synthetic pharmaceutical claims. Position wellness as biological mastery and personal empowerment.

Conversion Architecture:
- The PRIMARY objective is driving audiences to {config.WEBSITE_URL} (specifically the Podcasts archive page at {config.PODCASTS_URL}).
- Certified Health Coach & Product Orders: Always provide the dedicated hotline: {config.HEALTH_COACH_PHONE} for viewers who need certified health coach guidance, have questions, or want to order products.
- For TikTok/Instagram: Tell viewers to tap the link in bio for full episode archives & Academy membership, and call {config.HEALTH_COACH_PHONE} for certified health coach guidance or to order products.
- For X/Twitter: Include the direct link ({config.PODCASTS_URL}) and mention coach help/orders at {config.HEALTH_COACH_PHONE}, keeping text under 260 characters.
"""

import time

from src.video_cutter import get_media_duration_seconds

CANDIDATE_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]

def call_gemini_with_fallback(client, contents, schema, temperature=0.2) -> str:
    """Tries models in order with retry on temporary 503 high demand spikes."""
    last_err = None
    for model_name in CANDIDATE_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                        temperature=temperature,
                    ),
                )
                return response.text
            except Exception as e:
                last_err = e
                err_str = str(e)
                if "503" in err_str or "UNAVAILABLE" in err_str or "capacity" in err_str:
                    time.sleep(2 * (attempt + 1))
                    continue
                # If non-capacity error (e.g. 404), break to next model
                break
    raise last_err

def analyze_raw_media(file_path: str) -> LongFormAnalysis:
    client = get_gemini_client()
    uploaded_file = client.files.upload(file=file_path)
    
    duration_sec = get_media_duration_seconds(file_path)
    mins = int(duration_sec // 60)
    secs = int(duration_sec % 60)
    max_time_str = f"{mins:02d}:{secs:02d}"

    prompt = f"""
    {SYSTEM_EDITORIAL_RULES}
    Analyze this video/audio media from Pharmacist Ben's broadcast.
    CRITICAL CONSTRAINT: This audio sample is exactly {max_time_str} ({int(duration_sec)} seconds) in length.
    All segment clip proposals MUST have start_time and end_time strictly between 00:00 and {max_time_str}. Do NOT propose timestamps beyond {max_time_str}.
    1. Identify 1 to 2 distinct, highly engaging 30-60 second segments focused on root-cause biology, cellular health, or nutrition.
    2. For each segment, provide exact start and end timestamps (format MM:SS, strictly between 00:00 and {max_time_str}), an on-screen hook headline, a burned visual CTA banner directing to PharmacistBensAcademy.com, and platform-tailored copy.
    3. Generate an educational multiple-choice quiz question with 4 options, the correct index (0-3), and an insightful explanation for a community learning module.
    """
    
    text_resp = call_gemini_with_fallback(client, [uploaded_file, prompt], LongFormAnalysis, temperature=0.2)
    return LongFormAnalysis.model_validate_json(text_resp)

def generate_captions_for_existing_short(file_path: str) -> ExistingShortCaptions:
    client = get_gemini_client()
    uploaded_file = client.files.upload(file=file_path)
    
    prompt = f"""
    {SYSTEM_EDITORIAL_RULES}
    Watch/listen to this short video.
    1. Extract a punchy upper video hook headline (max 6 words, all-caps or high-impact title).
    2. Propose a lower-third CTA banner text (e.g. "Full Archives @ PharmacistBensAcademy.com").
    3. Generate 3 platform-tailored copy variants:
       - caption_tiktok: Engaging hook + curiosity trigger + CTA to link-in-bio to explore the podcast archive.
       - caption_instagram: Deeper educational context + hashtags + CTA to link-in-bio.
       - post_x: Punchy, authoritative summary under 250 characters with direct link: {config.PODCASTS_URL}.
    """
    
    text_resp = call_gemini_with_fallback(client, [uploaded_file, prompt], ExistingShortCaptions, temperature=0.3)
    return ExistingShortCaptions.model_validate_json(text_resp)

