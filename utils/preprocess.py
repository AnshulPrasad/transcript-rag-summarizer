import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)


def load_text_corpus(txt_dir: Path) -> tuple[list[Path], list[str]]:
    """Load a corpus of text files from a directory."""
    transcripts = []
    file_paths = []

    for file_path in txt_dir.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")
        transcripts.append(text)
        file_paths.append(file_path)

    logger.info("Collected %d transcripts", len(file_paths))
    return file_paths, transcripts


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping word-level chunks.

    Args:
        text: input text
        chunk_size: words per chunk
        overlap: words shared between consecutive chunks

    Returns:
        list of chunk strings (chunks shorter than 50 words are dropped)
    """
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if len(chunk.split()) >= 50:   # drop tiny tail chunks
            chunks.append(chunk)
    return chunks


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
