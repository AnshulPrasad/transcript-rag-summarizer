import faiss
import pickle
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder

from config import TRANSCRIPT_INDEX

logger = logging.getLogger(__name__)

EMBED_MODEL   = "BAAI/bge-small-en-v1.5"
RERANK_MODEL  = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CHUNKS_PKL    = "data/chunks.pkl"

# Load models once at startup (lightweight, always safe)
_embed_model   = SentenceTransformer(EMBED_MODEL)
_rerank_model  = CrossEncoder(RERANK_MODEL)

# Load index and chunks lazily on first query
_index = None
_chunks: list[str] = []


def _load_index_and_chunks():
    global _index, _chunks
    if _index is not None:
        return
    _index = faiss.read_index(TRANSCRIPT_INDEX)
    with open(CHUNKS_PKL, "rb") as f:
        _chunks = pickle.load(f)
    logger.info("Loaded FAISS index and %d chunks", len(_chunks))


def retrieve_transcripts(
    query: str,
    top_k: int = 20,
    retrieve_k: int = 30,
) -> list[str]:
    """
    1. Embed query and retrieve top retrieve_k chunks from FAISS.
    2. Rerank with cross-encoder and return top_k best chunks.
    """
    _load_index_and_chunks()

    # Step 1 — dense retrieval
    query_embedding = _embed_model.encode(
        [query], normalize_embeddings=True
    )
    _, indices = _index.search(query_embedding, retrieve_k)

    candidates = [_chunks[i] for i in indices[0] if i != -1]
    if not candidates:
        return []

    # Step 2 — rerank
    pairs = [[query, c] for c in candidates]
    scores = _rerank_model.predict(pairs)
    ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)

    results = [text for _, text in ranked[:top_k]]
    logger.info("Retrieved %d chunks after reranking (from %d candidates)", len(results), len(candidates))
    return results