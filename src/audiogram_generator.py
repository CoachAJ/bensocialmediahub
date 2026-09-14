import os
import subprocess
from src.video_cutter import escape_ffmpeg_text, get_font_file, parse_time_to_seconds

def render_audiogram_motion_video(
    audio_path: str,
    start_time: str,
    end_time: str,
    show_title: str,
    quote_hook: str,
    cta_text: str,
    output_path: str,
    output_gif: bool = False
):
    """
    Takes an audio episode segment and generates a 1080x1920 (9:16) vertical motion video
    featuring a live animated audio waveform, show badge, quote hook, and CTA banner.
    Optionally exports as an animated GIF.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    start_sec = parse_time_to_seconds(start_time)
    duration = max(1.0, parse_time_to_seconds(end_time) - start_sec)
    
    clean_title = escape_ffmpeg_text(show_title)
    clean_quote = escape_ffmpeg_text(quote_hook)
    clean_cta = escape_ffmpeg_text(cta_text)
    font_path = get_font_file()
    font_arg = f":fontfile='{font_path}'" if font_path else ""

    # Complex filter:
    # 1. Generate dark background: color=c=#0f172a:s=1080x1920
    # 2. Draw Show Header badge
    # 3. Draw Central Quote/Hook
    # 4. Generate dynamic live audio waveform from audio stream: showwaves=s=920x280:mode=cline:colors=0x38bdf8:rate=25
    # 5. Overlay waveform in lower third
    # 6. Draw bottom CTA banner
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

    if output_gif:
        # High quality GIF generation using palettegen/paletteuse
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-t", str(duration),
            "-i", audio_path,
            "-filter_complex", f"{filter_complex};[v]split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-r", "15",
            output_path
        ]
    else:
        # 9:16 H.264 Vertical MP4
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-t", str(duration),
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "0:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audiogram generation failed:\n{result.stderr}")
