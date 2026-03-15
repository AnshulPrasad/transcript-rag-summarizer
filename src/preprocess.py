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