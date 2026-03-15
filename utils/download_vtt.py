import subprocess
from pathlib import Path


def download_channel_subtitles(channel_url: str, output_dir: Path, language: str = "en") -> None:
    """
    Download subtitles of all the videos from a Youtube channel

    Args:
        channel_url (str): url of the youtube channel
        output_dir (str): output directory where the subtitles will be stored
        language (str): laguage of the subtile to be retrieved
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    archive_file = output_dir / "archive.txt"
    archive_file.touch(exist_ok=True)  # ← create if doesn't exist

    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-lang", language,
        "--sub-format", "vtt",
        "--limit-rate", "500K",
        "--sleep-interval", "10",
        "--max-sleep-interval", "30",
        "--retries", "infinite",
        "--fragment-retries", "infinite",
        "--force-write-archive",   # ← force write even for subtitle-only downloads
        "--retry-sleep", "429:60",
        "--ignore-errors",             # ← don't stop on errors
        "--no-abort-on-error",         # ← keep going after failures
        "--download-archive", str(archive_file),
        "-o", str(output_dir / "%(id)s.%(ext)s"),
        channel_url,
    ]

    subprocess.run(cmd, check=True)