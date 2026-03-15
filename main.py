import logging
import pickle
from pathlib import Path

from src.download_vtt import download_channel_subtitles
from src.vtt_to_txt import vtt_to_txt
from src.retrieve_context import retrieve_transcripts
from src.generate_response import generate_response
from src.embed_transcripts import embedding
from src.token import trim_to_token_limit, count_tokens
from config import CHANNEL_URLS, MAX_CONTEXT_TOKENS, VTT_DIR, TXT_DIR, TRANSCRIPT_INDEX, RETRIEVED_TRANSCRIPTS_FILE, RESPONSE_FILE, \
    FILE_PATHS, TRANSCRIPTS, CHUNKS_PKL

logger = logging.getLogger(__name__)

def stage_download() -> None:
    for channel_url in CHANNEL_URLS:
        try:
            download_channel_subtitles(channel_url, VTT_DIR, language="en")
        except Exception:
            logger.exception("Failed to download subtitles for %s", channel_url)


def stage_persist(file_paths, transcripts) -> None:
    with open(FILE_PATHS, "wb") as f:
        pickle.dump(file_paths, f)
    with open(TRANSCRIPTS, "wb") as f:
        pickle.dump(transcripts, f)


def stage_retrieve(query: str, k: int = 20) -> list[str]:
    results = retrieve_transcripts(query, k)
    if not results:
        logger.warning("No relevant transcripts found")
    return results

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

def write_retrieved_transcripts(retrieved_transcripts: list[str], file_paths: list[Path]) -> None:
    try:
        with RETRIEVED_TRANSCRIPTS_FILE.open("w", encoding="utf-8") as f:
            for i, (path, transcript) in enumerate(zip(file_paths, retrieved_transcripts), start=1):
                video_id = path.stem.split(".")[0]
                f.write(f"Video id: {video_id}\nTranscript {i}:\n{transcript}\n")
    except Exception:
        logger.exception("Failed to write retrieved transcripts")


def write_response(response):
    try:
        RESPONSE_FILE.write_text(response, encoding="utf-8")
        logger.info("Response written to %s", RESPONSE_FILE)

    except Exception:
        logger.exception("Failed to write response")


def main() -> None:
    query = input("Enter query:\n").strip()
    if not query:
        logger.error("Query cannot be empty")
        return

    stage_download()
    vtt_to_txt(VTT_DIR, TXT_DIR)
    file_paths, transcripts = load_text_corpus(TXT_DIR)
    stage_persist(file_paths, transcripts)

    with open(FILE_PATHS, "rb") as f:
        file_paths = pickle.load(f)
    with open(TRANSCRIPTS, "rb") as f:
        transcripts = pickle.load(f)
    file_paths = [Path(p) for p in file_paths]

    embedding(transcripts, TRANSCRIPT_INDEX, CHUNKS_PKL)

    retrieved = stage_retrieve(query, file_paths, transcripts)
    if not retrieved:
        return

    write_retrieved_transcripts(retrieved, file_paths)
    full_context = " ".join(retrieved)
    limit_context = trim_to_token_limit(full_context, MAX_CONTEXT_TOKENS)
    context_str = " ".join(limit_context.split("\n"))

    response = generate_response(query, limit_context)
    write_response("\n".join([f"Received query: {query}", f"Context: {context_str}", f"Response: {response}"]))

    logger.info("Full_context: %d tokens, %d words", count_tokens(full_context), len(full_context.split(" ")), )
    logger.info("Limit_context: %d tokens, %d words", count_tokens(limit_context), len(limit_context.split(" ")))
    # retrieved = stage_retrieve(query)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s]: %(message)s", )
    main()