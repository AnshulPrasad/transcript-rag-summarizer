import faiss
import pickle
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder
logger = logging.getLogger(__name__)

class Context:
    def __init__(self, chunk_faiss: Path, chunk_pkl: Path):
        self.chunk_faiss = chunk_faiss
        self.chunk_pkl = chunk_pkl
        self.embed_model   = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.rerank_model  = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

        # Load index and chunks lazily on first query
        self.index = None
        self.chunks: list[str] = []

    def load_index_and_chunks(self):
        if self.index is not None:
            return
        self.index = faiss.read_index(str(self.chunk_faiss))
        with open(self.chunk_pkl, "rb") as f:
            self.chunks = pickle.load(f)
        logger.info("Loaded FAISS index and %d chunks", len(self.chunks))

    def retrieve_chunks(self, query, top_k, retrieve_k) -> list[str]:
        self.load_index_and_chunks()

        # Step 1 — dense retrieval
        query_embedding = self.embed_model.encode([query], normalize_embeddings=True)
        _, indices = self.index.search(query_embedding, retrieve_k)
        candidates = [self.chunks[i] for i in indices[0] if i != -1]
        if not candidates:
            return []

        # Step 2 — rerank
        pairs = [[query, c] for c in candidates]
        scores = self.rerank_model.predict(pairs)
        ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
        results = [text for _, text in ranked[:top_k]]
        logger.info("Retrieved %d chunks after reranking (from %d candidates)", len(results), len(candidates))
        return results