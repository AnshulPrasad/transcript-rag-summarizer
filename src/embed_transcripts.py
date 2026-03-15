import faiss
import pickle
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
logger = logging.getLogger(__name__)

EMBED_MODEL = "BAAI/bge-small-en-v1.5"   # better than all-MiniLM-L6-v2, same speed

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

def embedding(
    transcripts: list[str],
    transcript_index: str,           # path to .faiss FILE (not dir)
    chunks_pkl: str = "data/chunks.pkl",
) -> None:
    """
    Chunk every transcript, embed all chunks, build FAISS index.

    Saves:
        transcript_index  — FAISS flat-L2 index file
        chunks_pkl        — pickle of all chunk strings (same order as index)
    """
    # 1. Chunk all transcripts
    all_chunks: list[str] = []
    for text in transcripts:
        all_chunks.extend(chunk_text(text))
    logger.info("Total chunks after splitting: %d", len(all_chunks))

    # 2. Embed
    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(all_chunks, show_progress_bar=True, normalize_embeddings=True)

    # 3. Build FAISS index  (fix: write to FILE, not mkdir)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)   # inner-product works well with normalized embeddings
    index.add(embeddings)
    faiss.write_index(index, str(transcript_index))   # ← was: transcript_index.mkdir() — BUG FIXED

    # 4. Save chunks so retrieval can map index → text
    Path(chunks_pkl).parent.mkdir(parents=True, exist_ok=True)
    with open(chunks_pkl, "wb") as f:
        pickle.dump(all_chunks, f)

    logger.info("Embedding completed. Index: %s  Chunks: %s", transcript_index, chunks_pkl)