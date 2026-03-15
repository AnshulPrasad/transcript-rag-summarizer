import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)

# Matches inline timing/formatting tags like <00:00:09.360> and <c>text</c>
_TAG_RE = re.compile(r'<[^>]+>')
# Matches VTT timestamp lines like "00:00:08.360 --> 00:00:21.509 align:start position:0%"
_TIMESTAMP_RE = re.compile(r'^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->')

NOISE_LINES = {
    "WEBVTT", "Kind:", "Language:",
    "[Music]", "[music]", "[Applause]", "[Laughter]",
    "[Cheering]", "[Clapping]", "[Audience Laughing]",
    "[Audience Applause]", "[Background Noise]",
    "[प्रशंसा]", "[तालियाँ]", "[संगीत]",
    "[हँसी]", "[जयकारे]", "[शोर]", "[पृष्ठभूमि संगीत]",
}


def vtt_to_clean_text(vtt_file: Path, txt_file: Path) -> None:
    """
    Convert a WebVTT subtitle file into cleaned plain text.
    - Removes timestamp lines
    - Strips inline timing tags like <00:00:09.360><c>
    - Removes noise markers
    - Deduplicates consecutive identical lines
    """
    seen_lines = set()
    cleaned = []

    with vtt_file.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Skip timestamp lines
            if _TIMESTAMP_RE.match(stripped):
                continue

            # Skip header and noise lines
            if any(stripped.startswith(k) for k in NOISE_LINES):
                continue

            # Strip inline tags → clean text
            clean = _TAG_RE.sub('', stripped).strip()

            # Skip empty after stripping, single spaces, or pure whitespace
            if not clean or clean == ' ':
                continue

            # Deduplicate — skip if we've seen this exact line already
            if clean in seen_lines:
                continue

            seen_lines.add(clean)
            cleaned.append(clean)

    txt_file.write_text('\n'.join(cleaned) + '\n', encoding='utf-8')
    logger.info("Converted %s → %s (%d lines)", vtt_file.name, txt_file.name, len(cleaned))


def vtt_to_txt(vtt_dir: Path, txt_dir: Path) -> None:
    """
    Convert Youtube file format .vtt (WebVTT or Web Video Text to Track) to text file format .txt

    Args:
        vtt_dir (Path): directory which contain all the .vtt files
        txt_dir (Path): directory in which the converted .txt files will be saved
    """

    txt_dir.mkdir(parents=True, exist_ok=True)

    for vtt_path in vtt_dir.glob("*.vtt"):
        txt_path = txt_dir / vtt_path.with_suffix(".txt").name

        if txt_path.exists():
            logger.info("Skipping %s (already exists)", txt_path.name)
            continue

        vtt_to_clean_text(vtt_path, txt_path)

    logger.info("Completed %s → %s conversion", vtt_dir.name, txt_dir.name)
