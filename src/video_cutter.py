import os
import re
import subprocess
import sys

def get_media_duration_seconds(file_path: str) -> float:
    """Returns the duration of an audio or video file in seconds using ffprobe."""
    if not os.path.exists(file_path):
        return 0.0
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            return float(res.stdout.strip())
    except Exception:
        pass
    return 600.0  # Fallback to 10 minutes default

def parse_time_to_seconds(time_str: str, max_duration: float | None = None) -> float:
    """Parses timestamps like MM:SS, HH:MM:SS, or seconds into a safe float."""
    if not time_str:
        return 0.0
    clean = str(time_str).strip()
    match = re.search(r"(\d+):(\d+)(?::(\d+))?", clean)
    if match:
        groups = [g for g in match.groups() if g is not None]
        if len(groups) == 2:
            val = float(groups[0]) * 60 + float(groups[1])
        elif len(groups) == 3:
            val = float(groups[0]) * 3600 + float(groups[1]) * 60 + float(groups[2])
        else:
            val = float(groups[0])
    else:
        num_match = re.search(r"(\d+(?:\.\d+)?)", clean)
        val = float(num_match.group(1)) if num_match else 0.0

    if max_duration and max_duration > 0:
        val = min(val, max_duration)
    return max(0.0, val)

def escape_ffmpeg_text(text: str) -> str:
    """Escapes special characters for FFmpeg drawtext filter."""
    if not text:
        return ""
    # Remove newlines
    text = text.replace("\r", " ").replace("\n", " ")
    # Replace straight apostrophes with typographic apostrophes to prevent string termination
    text = text.replace("'", "’")
    # Replace double quotes
    text = text.replace('"', "”")
    # Escape backslashes, colons, and percent signs
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("%", "\\%")
    return text.strip()

def get_font_file() -> str | None:
    """Detects available font file for current OS (Windows or Linux)."""
    candidates = [
        # Ubuntu / Debian (GitHub Actions)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        # Windows
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            # Format path for ffmpeg (escape colon on Windows)
            return c.replace("\\", "/").replace(":", "\\:")
    return None

def render_vertical_short(
    input_video: str,
    start_time: str,
    end_time: str,
    hook_text: str,
    cta_text: str,
    output_path: str
):
    """
    Cuts video segment, scales/crops to 9:16 vertical (1080x1920),
    and burns in upper headline hook and lower-third CTA banner.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    start_sec = parse_time_to_seconds(start_time)
    duration = max(1.0, parse_time_to_seconds(end_time) - start_sec)
    
    clean_hook = escape_ffmpeg_text(hook_text)
    clean_cta = escape_ffmpeg_text(cta_text)
    font_path = get_font_file()
    
    font_arg = f":fontfile='{font_path}'" if font_path else ""

    # 1. Scale/crop to 1080x1920 (9:16)
    # 2. Draw upper hook headline
    # 3. Draw bottom CTA banner
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        f"drawtext=text='{clean_hook}'{font_arg}:fontcolor=white:fontsize=46:box=1:"
        "boxcolor=black@0.65:boxborderw=12:x=(w-text_w)/2:y=180,"
        f"drawtext=text='{clean_cta}'{font_arg}:fontcolor=yellow:fontsize=38:box=1:"
        "boxcolor=black@0.75:boxborderw=10:x=(w-text_w)/2:y=h-240[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-t", str(duration),
        "-i", input_video,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-ac", "2",
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed with code {result.returncode}:\n{result.stderr}")
