import os
import sys
import argparse
import datetime
from src.config import config
from src.drive_sync import (
    fetch_unprocessed_files,
    download_file,
    upload_public_clip,
    load_manifest,
    save_manifest
)
from src.gemini_processor import (
    analyze_raw_media,
    generate_captions_for_existing_short
)
from src.video_cutter import render_vertical_short
from src.audiogram_generator import render_audiogram_motion_video
from src.rss_ingest import (
    fetch_unprocessed_podcast_episodes,
    download_podcast_audio_sample,
    download_podcast_image
)
from src.image_generator import generate_clip_topic_image
from src.buffer_publisher import (
    get_buffer_profiles,
    can_schedule,
    dispatch_platform_post
)
from src.skool_generator import render_skool_quiz_embed
from src.sheets_reporter import log_event

def log_progress(stage: str, message: str):
    """Outputs standardized log messages for CLI and Master Hub Web UI."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{stage.upper()}] {message}", flush=True)

def run_pipeline(mode: str = "all", max_items_per_source: int = 2, visual_style: str = "alternate"):
    log_progress("init", f"Starting Pharmacist Ben Promotion Engine in '{mode}' mode (Visual Style: {visual_style})...")
    manifest = load_manifest()
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    style_counter = manifest.get("visual_style_counter", 0)

    # Discover connected Buffer profiles and their platforms
    profiles = get_buffer_profiles()
    profile_mapping = config.get_profile_mapping()
    
    # If no profile IDs in config, use discovered profile IDs
    target_profiles = config.BUFFER_PROFILE_IDS or [p["id"] for p in profiles]
    log_progress("buffer", f"Targeting {len(target_profiles)} Buffer channels. Profile IDs: {target_profiles}")

    # ==========================================
    # TRACK 1: Existing Google Drive Shorts (<3m)
    # ==========================================
    if mode in ["all", "shorts"]:
        log_progress("drive", f"Scanning Google Drive shorts folder: '{config.GDRIVE_EXISTING_FOLDER_ID or 'Not Configured'}'")
        try:
            existing_files = fetch_unprocessed_files(config.GDRIVE_EXISTING_FOLDER_ID, "existing_shorts")
        except Exception as e:
            log_progress("drive_warn", f"Could not scan Drive folder (check credentials/folder ID): {e}")
            existing_files = []

        log_progress("drive", f"Found {len(existing_files)} new unprocessed shorts in Google Drive.")

        for file in existing_files[:max_items_per_source]:
            file_id = file["id"]
            file_name = file["name"]
            log_progress("process_short", f"Processing uploaded short: '{file_name}' ({file_id})")

            local_raw_path = f"tmp/raw_shorts/{file_name}"
            download_file(file_id, local_raw_path, item_meta=file)

            log_progress("gemini", f"Analyzing video with Gemini 2.5 Flash for hooks and platform copy...")
            captions = generate_captions_for_existing_short(local_raw_path)

            output_clip_path = f"output/shorts/{file_id}_burned.mp4"
            log_progress("ffmpeg", f"Rendering vertical 9:16 video with burned hook & CTA banner...")
            try:
                render_vertical_short(
                    input_video=local_raw_path,
                    start_time="00:00",
                    end_time="02:59",
                    hook_text=captions.hook_headline,
                    cta_text=captions.burned_cta_text or "Full Archive @ PharmacistBensAcademy.com",
                    output_path=output_clip_path
                )
            except Exception as e:
                log_progress("ffmpeg_warn", f"Video rendering encountered an error: {e}. Proceeding with source clip.")
                output_clip_path = local_raw_path

            # Upload newly branded, burned vertical short to GitHub Releases CDN
            media_url = upload_public_clip(output_clip_path, f"ben_short_{file_id}.mp4") or file.get("direct_url")
            log_progress("hosting", f"Direct video asset URL for Buffer (GitHub CDN): {media_url}")

            # Schedule to Buffer profiles (respecting 10-post queue cap)
            short_scheduled = False
            for pid in target_profiles:
                platform_type = profile_mapping.get(pid, "social")
                if can_schedule(pid, limit=10):
                    log_progress("buffer_dispatch", f"Queueing to Buffer profile {pid} ({platform_type})...")
                    update = dispatch_platform_post(
                        profile_id=pid,
                        platform_hint=platform_type,
                        caption_tiktok=captions.caption_tiktok,
                        caption_instagram=captions.caption_instagram,
                        post_x=captions.post_x,
                        media_url=media_url
                    )
                    up_id = str(update.get("updates", [{}])[0].get("id", "queued"))
                    log_event(now_str, file_name, "Drive Short (Video)", "Scheduled", up_id, config.WEBSITE_URL)
                    if update.get("success"):
                        short_scheduled = True
                else:
                    log_progress("buffer_skip", f"Queue full (10 posts) for profile {pid}. Skipping dispatch.")

            if short_scheduled:
                manifest["existing_shorts"].append(file_id)
                save_manifest(manifest)
                log_progress("short_done", f"Completed short '{file_name}'. Manifest updated.")
            else:
                log_progress("short_retry", f"Short '{file_name}' queue was skipped (profiles full or dry run). Will retry next run.")

    # ==========================================
    # TRACK 2: Podcast RSS Feeds (The 3 Shows)
    # ==========================================
    if mode in ["all", "podcasts"]:
        log_progress("rss", "Checking podcast RSS feeds (Pharmacist Ben's Bytes, The Mineral Way, The Art of Aging Well)...")
        new_episodes = fetch_unprocessed_podcast_episodes(max_per_feed=3)
        log_progress("rss", f"Found {len(new_episodes)} new podcast episodes across feeds.")

        for ep in new_episodes[:max_items_per_source]:
            safe_id = "".join(c for c in ep.episode_id if c.isalnum())[-12:]
            log_progress("podcast_ep", f"Processing episode from '{ep.podcast_name}': {ep.title}")

            local_audio_path = f"tmp/audio/{safe_id}.mp3"
            log_progress("audio_dl", f"Downloading audio sample from episode...")
            try:
                download_podcast_audio_sample(ep.audio_url, local_audio_path)
            except Exception as e:
                log_progress("audio_warn", f"Could not download audio stream: {e}. Skipping episode.")
                continue

            log_progress("gemini", "Analyzing episode audio with Gemini for golden nugget & Skool quiz...")
            try:
                analysis = analyze_raw_media(local_audio_path)
            except Exception as e:
                log_progress("gemini_warn", f"Gemini audio analysis failed: {e}")
                continue

            # 1. Generate Skool Community Quiz Embed
            quiz_path = f"output/quizzes/{safe_id}_quiz.html"
            log_progress("quiz", f"Generating interactive Skool quiz embed at {quiz_path}...")
            render_skool_quiz_embed(
                question=analysis.quiz_question,
                options=analysis.quiz_options,
                correct_idx=analysis.quiz_correct_index,
                explanation=analysis.quiz_explanation,
                output_path=quiz_path
            )

            # 2. Render Vertical 9:16 Audiogram Motion Video with Alternating Visual Imagery
            local_show_image_path = f"tmp/images/{safe_id}_show.jpg"
            chosen_show_image_path = None
            if ep.image_url:
                log_progress("image_dl", f"Downloading cover artwork for '{ep.title}'...")
                downloaded_img = download_podcast_image(ep.image_url, local_show_image_path)
                if downloaded_img and os.path.exists(downloaded_img):
                    chosen_show_image_path = downloaded_img

            if not chosen_show_image_path and os.path.exists("assets/pharmacist_ben.jpg"):
                chosen_show_image_path = "assets/pharmacist_ben.jpg"

            audiogram_scheduled = False
            for idx, clip in enumerate(analysis.clips[:1]):
                audiogram_path = f"output/audiograms/{safe_id}_clip_{idx}.mp4"
                
                # Determine alternating visual style:
                # Even counter: Show artwork / brand portrait
                # Odd counter: Gemini-crafted topic illustration
                current_style_idx = style_counter + idx
                if visual_style == "show":
                    is_topic_style = False
                elif visual_style == "topic":
                    is_topic_style = True
                else:
                    is_topic_style = (current_style_idx % 2 == 1)

                if is_topic_style:
                    log_progress("image_ai", f"Generating Gemini topic visual for '{clip.hook_headline}'...")
                    topic_img_path = f"tmp/images/{safe_id}_topic_{idx}.png"
                    chosen_image_path = generate_clip_topic_image(
                        prompt=clip.visual_concept_prompt or clip.hook_headline,
                        keywords=clip.topic_search_keywords or clip.hook_headline,
                        output_path=topic_img_path,
                        fallback_image=chosen_show_image_path
                    )
                    badge_label = "PHARMACIST BEN | HEALTH DEEP DIVE"
                    badge_color = "0x10b981"  # Emerald green for topical deep dive
                    style_label = "Gemini Topic Illustration"
                else:
                    log_progress("image_show", f"Using show artwork for '{ep.podcast_name}'...")
                    chosen_image_path = chosen_show_image_path
                    badge_label = f"PHARMACIST BEN | {ep.podcast_name}"
                    badge_color = "0x38bdf8"  # Electric cyan for show cover art
                    style_label = "Show Cover Artwork"

                log_progress("ffmpeg", f"Rendering 9:16 audiogram for '{clip.hook_headline}' ({style_label})...")
                try:
                    render_audiogram_motion_video(
                        audio_path=local_audio_path,
                        start_time=clip.start_time,
                        end_time=clip.end_time,
                        show_title=ep.podcast_name,
                        quote_hook=clip.hook_headline,
                        cta_text="Full Archive @ PharmacistBensAcademy.com",
                        output_path=audiogram_path,
                        image_path=chosen_image_path,
                        badge_label=badge_label,
                        badge_color=badge_color,
                        output_gif=False
                    )
                except Exception as e:
                    log_progress("ffmpeg_warn", f"Audiogram render failed: {e}")
                    continue

                # Upload to GitHub Releases CDN for public Buffer access
                log_progress("hosting", f"Publishing {style_label} audiogram to GitHub CDN...")
                try:
                    media_url = upload_public_clip(audiogram_path, f"audiogram_{safe_id}_{idx}.mp4")
                except Exception as e:
                    log_progress("hosting_warn", f"Could not publish audiogram to GitHub CDN: {e}")
                    media_url = None

                # Dispatch to Buffer
                for pid in target_profiles:
                    platform_type = profile_mapping.get(pid, "social")
                    if can_schedule(pid, limit=10):
                        log_progress("buffer_dispatch", f"Queueing podcast audiogram ({style_label}) to Buffer ({platform_type})...")
                        update = dispatch_platform_post(
                            profile_id=pid,
                            platform_hint=platform_type,
                            caption_tiktok=clip.caption_tiktok,
                            caption_instagram=clip.caption_instagram,
                            post_x=clip.post_x,
                            media_url=media_url
                        )
                        up_id = str(update.get("updates", [{}])[0].get("id", "queued"))
                        log_event(now_str, f"{ep.title} [Clip {idx}]", f"Podcast Audiogram ({style_label})", "Scheduled", up_id, config.PODCASTS_URL)
                        if update.get("success"):
                            audiogram_scheduled = True
                    else:
                        log_progress("buffer_skip", f"Queue full (10 posts) for profile {pid}. Skipping.")

            if audiogram_scheduled:
                manifest["podcast_episodes"].append(ep.episode_id)
                manifest["visual_style_counter"] = style_counter + 1
                save_manifest(manifest)
                log_progress("podcast_done", f"Finished episode '{ep.title}'. Manifest saved (next style: {'Show Cover Art' if (style_counter + 1) % 2 == 0 else 'Gemini Topic Art'}).")
            else:
                log_progress("podcast_retry", f"Episode '{ep.title}' will be retried on next run (audiogram not yet scheduled).")

    log_progress("complete", "Pipeline execution run finished successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pharmacist Ben Promotion Engine Orchestrator")
    parser.add_argument("--mode", choices=["all", "shorts", "podcasts", "dry-run"], default="all", help="Execution mode")
    parser.add_argument("--max", type=int, default=2, help="Max items per source to process")
    parser.add_argument(
        "--style",
        choices=["alternate", "show", "topic"],
        default="alternate",
        help="Visual imagery style for audiograms: 'alternate' (alternates show art & topic art), 'show' (always show art), 'topic' (always Gemini topic art)"
    )
    args = parser.parse_args()

    run_pipeline(mode=args.mode, max_items_per_source=args.max, visual_style=args.style)
