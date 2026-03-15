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
        "--sub-lang",
        language,
        "--sub-format",
        "vtt",
        "--js-runtimes",
        "node",
        "--limit-rate",
        "500K",
        "--sleep-interval",
        "10",
        "--max-sleep-interval",
        "30",
        "--retries",
        "infinite",
        "--fragment-retries",
        "infinite",
        "--retry-sleep",
        "429:60",
        "--download-archive",
        str(output_dir / "archive.txt"),
        "-o",
        str(output_dir / "%(id)s.%(ext)s"),
        "--download-archive", str(archive_file),
        channel_url,
    ]

    subprocess.run(cmd, check=True)
