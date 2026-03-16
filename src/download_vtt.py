import subprocess
from pathlib import Path

class Download:
    def __init__(self, channel_id: str, output_dir: Path, language: str = "en"):
        self.channel_url = f"https://www.youtube.com/@{channel_id}/videos"
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.language = language
        self.archive_file = self.output_dir / "archive.txt"
        self.archive_file.touch(exist_ok=True)

    def download_channel_subtitles(self) -> None:
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-lang", self.language,
            "--sub-format", "vtt",
            "--limit-rate", "500K",
            "--sleep-interval", "10",
            "--max-sleep-interval", "30",
            "--retries", "infinite",
            "--fragment-retries", "infinite",
            "--force-write-archive",
            "--retry-sleep", "429:60",
            "--ignore-errors",
            "--no-abort-on-error",
            "--download-archive", str(self.archive_file),
            "-o", str(self.output_dir / "%(id)s.%(ext)s"),
            self.channel_url,
        ]
        subprocess.run(cmd, check=False)