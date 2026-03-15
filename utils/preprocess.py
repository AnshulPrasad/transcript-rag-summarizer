import logging
from pathlib import Path

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


KEYWORDS = {
    "WEBVTT", "Kind", "Language", "-->", "<",
    "[Music]", "[music]", "[Applause]", "[Laughter]",
    "[Cheering]", "[Clapping]", "[Audience Laughing]",
    "[Audience Applause]", "[Background Noise]",
    "[प्रशंसा]", "[तालियाँ]", "[संगीत]",
    "[हँसी]", "[जयकारे]", "[शोर]", "[पृष्ठभूमि संगीत]",
}


def vtt_to_clean_text(vtt_file: Path, txt_file: Path) -> None:
    """Convert a WebVTT subtitle file into cleaned plain text."""
    with vtt_file.open("r", encoding="utf-8") as vtt, \
         txt_file.open("w", encoding="utf-8") as txt:
        for line in vtt:
            stripped = line.strip()
            if not stripped:
                continue
            if any(k in stripped for k in KEYWORDS):
                continue
            txt.write(stripped + "\n")
    logger.info("Converted %s → %s", vtt_file.name, txt_file.name)


def deduplicate_consecutive_lines(txt_dir: Path) -> None:
    """Remove consecutive duplicate lines from text files in a directory."""
    for file_path in txt_dir.glob("*.txt"):
        lines = file_path.read_text(encoding="utf-8").splitlines()
        cleaned = []
        previous = None
        for line in lines:
            if line != previous:
                cleaned.append(line)
            previous = line
        file_path.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    logger.info("Removed consecutive duplicates in %s", txt_dir)