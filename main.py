import logging
import pickle
from pathlib import Path

from src.download_vtt import download_channel_subtitles
from src.vtt_to_txt import vtt_to_txt
from src.preprocess import load_text_corpus
from src.retrieve_context import retrieve_transcripts
from src.generate_response import generate_response
from src.embed_transcripts import embedding
from config import CHANNEL_URLS, VTT_DIR, TXT_DIR, TRANSCRIPT_INDEX, RETRIEVED_TRANSCRIPTS_FILE, RESPONSE_FILE, \
    FILE_PATHS, TRANSCRIPTS, CHUNKS_PKL

logger = logging.getLogger(__name__)


def stage_query() -> str | None:
    query = input("Enter query:\n").strip()
    return query or None


def stage_download() -> None:
    for channel_url in CHANNEL_URLS:
        try:
            download_channel_subtitles(channel_url, VTT_DIR, language="en")
        except Exception:
            logger.exception("Failed to download subtitles for %s", channel_url)


def stage_preprocess() -> tuple[list[Path], list[str]]:
    vtt_to_txt(VTT_DIR, TXT_DIR)
    return load_text_corpus(TXT_DIR)


def stage_persist(file_paths, transcripts) -> None:
    with open(FILE_PATHS, "wb") as f:
        pickle.dump(file_paths, f)
    with open(TRANSCRIPTS, "wb") as f:
        pickle.dump(transcripts, f)


def stage_embed(transcripts: list[str]) -> None:
    embedding(transcripts, TRANSCRIPT_INDEX, CHUNKS_PKL)


def stage_retrieve(query: str, file_paths: list[Path], transcripts: list[str], k: int = 20) -> list[str]:
    results = retrieve_transcripts(query, file_paths, transcripts, k)
    if not results:
        logger.warning("No relevant transcripts found")
    return results


def stage_generate(query: str, context: str) -> str:
    return generate_response(query, context)


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
    query = stage_query()
    if not query:
        logger.error("Query cannot be empty")
        return

    stage_download()
    file_paths, transcripts = stage_preprocess()
    stage_persist(file_paths, transcripts)

    with open(FILE_PATHS, "rb") as f:
        file_paths = pickle.load(f)
    with open(TRANSCRIPTS, "rb") as f:
        transcripts = pickle.load(f)
    file_paths = [Path(p) for p in file_paths]

    stage_embed(transcripts)

    retrieved = stage_retrieve(query, file_paths, transcripts)
    if not retrieved:
        return

    write_retrieved_transcripts(retrieved, file_paths)
    full_context = " ".join(retrieved)
    limit_context = trim_to_token_limit(full_context, MAX_CONTEXT_TOKENS)
    context_str = " ".join(limit_context.split("\n"))

    response = stage_generate(query, limit_context)
    write_response("\n".join([f"Received query: {query}", f"Context: {context_str}", f"Response: {response}"]))

    logger.info("Full_context: %d tokens, %d words", count_tokens(full_context), len(full_context.split(" ")), )
    logger.info("Limit_context: %d tokens, %d words", count_tokens(limit_context), len(limit_context.split(" ")))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s]: %(message)s", )
    main()