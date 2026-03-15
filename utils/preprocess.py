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