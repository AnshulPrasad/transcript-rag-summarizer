import logging
import pickle
from pathlib import Path

from logger import setup_logging
from download_vtt import Download
from vtt_to_txt import Clean
from embed_transcripts import Embed
from retrieve_context import Context
from tokenizer import Tokenizer
from generate_response import Response
from config import CHANNEL_IDS, MAX_CONTEXT_TOKENS, VTT_DIR, TXT_DIR, CHUNK_FAISS, RETRIEVED_TRANSCRIPTS_FILE, RESPONSE_FILE, \
FILE_PKL, TRANSCRIPTS_PKL, CHUNK_PKL, MODEL, GROQ_API_KEY, SYSTEM_PROMPT, ENCODER

setup_logging()
logger = logging.getLogger(__name__)

def load_text_corpus(txt_dir: Path) -> tuple[list[Path], list[str]]:
    transcripts = []
    file_paths = []
    for file_path in sorted(txt_dir.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8")
        transcripts.append(text)
        file_paths.append(Path(file_path))
    logger.info("Collected %d transcripts", len(file_paths))
    return file_paths, transcripts

def write_retrieved_transcripts(retrieved_transcripts: list[str], file_paths: list[Path]) -> None:
    with RETRIEVED_TRANSCRIPTS_FILE.open("w", encoding="utf-8") as f:
        for i, (path, transcript) in enumerate(zip(file_paths, retrieved_transcripts), start=1):
            video_id = path.stem.split(".")[0]
            f.write(f"Video id: {video_id}\nTranscript {i}:\n{transcript}\n")

def main() -> None:
    # Query
    query = input("Enter query:\n").strip()
    if not query:
        logger.error("Query cannot be empty")
        return

    # Download
    for channel_id in CHANNEL_IDS:
        obj1 = Download(channel_id, VTT_DIR, language = "en")
        obj1.download_channel_subtitles()

    # Clean
    obj2 = Clean(VTT_DIR, TXT_DIR)
    obj2.vtt_to_txt()

    # Get file paths and transcripts
    file_paths, transcripts = load_text_corpus(TXT_DIR)
    with open(FILE_PKL, "wb") as f:
        pickle.dump(file_paths, f)
    with open(TRANSCRIPTS_PKL, "wb") as f:
        pickle.dump(transcripts, f)

    with open(FILE_PKL, "rb") as f:
        file_paths = pickle.load(f)

    # Embed
    obj3 = Embed(TRANSCRIPTS_PKL, CHUNK_FAISS, CHUNK_PKL)
    obj3.embedding()

    # Get context
    obj4 = Context(CHUNK_FAISS, CHUNK_PKL)
    retrieved = obj4.retrieve_chunks(query, top_k=20, retrieve_k=25)
    if not retrieved:
        return
    write_retrieved_transcripts(retrieved, file_paths)

    # Token limit prompt
    obj5 = Tokenizer(MODEL, ENCODER)
    full_context = " ".join(retrieved)
    limit_context = obj5.trim_to_token_limit(full_context, MAX_CONTEXT_TOKENS)
    context_str = " ".join(limit_context.split("\n"))
    logger.info("Full_context: %d tokens, %d words", obj5.count_tokens(full_context), len(full_context.split(" ")), )
    logger.info("Limit_context: %d tokens, %d words", obj5.count_tokens(limit_context), len(limit_context.split(" ")))

    # Response
    obj6 = Response(GROQ_API_KEY, MODEL, ENCODER, SYSTEM_PROMPT)
    response = obj6.generate_response(query, limit_context)
    logging.info("Total number of tokens in prompt: %s", obj5.count_tokens(query + SYSTEM_PROMPT + limit_context))
    write = "\n".join([f"Received query: {query}", f"Context: {context_str}", f"Response: {response}"])
    RESPONSE_FILE.write_text(write, encoding="utf-8")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s]: %(message)s", )
    main()