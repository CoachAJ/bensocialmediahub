import os
import subprocess
from src.video_cutter import escape_ffmpeg_text, get_font_file, parse_time_to_seconds, get_media_duration_seconds

def render_audiogram_motion_video(
    audio_path: str,
    start_time: str,
    end_time: str,
    show_title: str,
    quote_hook: str,
    cta_text: str,
    output_path: str,
    image_path: str | None = None,
    badge_label: str | None = None,
    badge_color: str = "0x38bdf8",
    output_gif: bool = False
):
    """
    Takes an audio episode segment and generates a 1080x1920 (9:16) vertical motion video.
    If image_path is provided:
      1. Renders an ambient blurred & darkened background from the image.
      2. Displays a sharp, framed artwork/topic card in the upper-center.
      3. Overlays show badge, bold quote hook, dynamic audio waveform, and CTA banner.
    If image_path is None or missing, falls back to a clean modern dark slate background.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    total_audio_sec = get_media_duration_seconds(audio_path)
    
    start_sec = parse_time_to_seconds(start_time, max_duration=total_audio_sec)
    end_sec = parse_time_to_seconds(end_time, max_duration=total_audio_sec)
    
    # If Gemini proposed a start time past the available sample, adjust to a valid window
    if total_audio_sec > 5 and start_sec >= (total_audio_sec - 5):
        start_sec = max(0.0, total_audio_sec - 45.0)
        end_sec = total_audio_sec

    duration = max(3.0, end_sec - start_sec)
    if total_audio_sec > 0:
        duration = min(duration, total_audio_sec - start_sec)
        duration = max(2.0, duration)
    
    clean_title = escape_ffmpeg_text(show_title)
    clean_quote = escape_ffmpeg_text(quote_hook)
    clean_cta = escape_ffmpeg_text(cta_text)
    header_text = escape_ffmpeg_text(badge_label) if badge_label else f"PHARMACIST BEN | {clean_title}"
    font_path = get_font_file()
    font_arg = f":fontfile='{font_path}'" if font_path else ""

    has_valid_image = bool(image_path and os.path.exists(image_path) and os.path.getsize(image_path) > 500)

    if has_valid_image:
        # Multi-layer layout with artwork/topic illustration:
        # 1. Ambient blurred background: scale/crop image to 1080x1920, heavy boxblur, darkened tint
        # 2. Centered crisp image card (620x620) with glowing border
        # 3. Header badge pill at y=170
        # 4. Central quote text at y=980
        # 5. Live animated audio waveform at y=1240
        # 6. Call-to-action banner at y=1640
        filter_complex = (
            "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "boxblur=25:5,drawbox=x=0:y=0:w=1080:h=1920:color=black@0.65:t=fill[ambient];"
            f"[1:v]scale=620:620:force_original_aspect_ratio=increase,crop=620:620,"
            f"pad=636:636:8:8:color={badge_color}@0.9[card];"
            "[ambient][card]overlay=(W-w)/2:270[bg0];"
            f"[bg0]drawtext=text='{header_text}'{font_arg}:fontcolor={badge_color}:fontsize=34:box=1:"
            "boxcolor=black@0.6:boxborderw=10:x=(w-text_w)/2:y=170[bg1];"
            f"[bg1]drawtext=text='{clean_quote}'{font_arg}:fontcolor=white:fontsize=46:box=1:"
            "boxcolor=black@0.7:boxborderw=14:x=(w-text_w)/2:y=980[bg2];"
            "[0:a]showwaves=s=920x240:mode=cline:colors=0x38bdf8@0.9:scale=sqrt:rate=25[wave];"
            "[bg2][wave]overlay=(W-w)/2:1240[v3];"
            f"[v3]drawtext=text='{clean_cta}'{font_arg}:fontcolor=yellow:fontsize=36:box=1:"
            "boxcolor=black@0.75:boxborderw=10:x=(w-text_w)/2:y=1640[v]"
        )
        input_args = [
            "-ss", str(start_sec),
            "-t", str(duration),
            "-i", audio_path,
            "-loop", "1",
            "-framerate", "25",
            "-i", image_path
        ]
    else:
        # Clean modern dark slate fallback layout
        filter_complex = (
            f"color=c=#090d16:s=1080x1920:d={duration}[bg];"
            f"[bg]drawtext=text='PHARMACIST BEN | {clean_title}'{font_arg}:fontcolor=0x38bdf8:fontsize=36:box=1:"
            "boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=220[bg1];"
            f"[bg1]drawtext=text='{clean_quote}'{font_arg}:fontcolor=white:fontsize=48:box=1:"
            "boxcolor=black@0.65:boxborderw=14:x=(w-text_w)/2:y=680[bg2];"
            "[0:a]showwaves=s=920x260:mode=cline:colors=0x38bdf8@0.9:scale=sqrt:rate=25[wave];"
            "[bg2][wave]overlay=(W-w)/2:1120[v3];"
            f"[v3]drawtext=text='{clean_cta}'{font_arg}:fontcolor=yellow:fontsize=38:box=1:"
            "boxcolor=black@0.75:boxborderw=10:x=(w-text_w)/2:y=1580[v]"
        )
        input_args = [
            "-ss", str(start_sec),
            "-t", str(duration),
            "-i", audio_path
        ]

    if output_gif:
        cmd = [
            "ffmpeg", "-y",
            *input_args,
            "-filter_complex", f"{filter_complex};[v]split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-r", "15",
            "-t", str(duration),
            output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            *input_args,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "0:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-ac", "2",
            "-t", str(duration),
            "-movflags", "+faststart",
            output_path
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audiogram generation failed:\n{result.stderr}")
