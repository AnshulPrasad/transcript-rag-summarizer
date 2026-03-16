import faiss
import pickle
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
logger = logging.getLogger(__name__)

class Embed:
    def __init__(self, transcripts: Path, chunk_index: Path, chunks_pkl: Path) -> None:
        self.transcripts = transcripts
        self.chunk_index = chunk_index
        self.chunks_pkl = chunks_pkl
        self.EMBED_MODEL = "BAAI/bge-small-en-v1.5"

    def chunk_text(self, text: str, chunk_size: int = 200, overlap: int = 50) -> list[str]:
        words = text.split()
        chunks = []
        step = chunk_size - overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i : i + chunk_size])
            if len(chunk.split()) >= 50:   # drop tiny tail chunks
                chunks.append(chunk)
        return chunks

    def embedding(self) -> None:
        # 1. Chunk all transcripts
        all_chunks: list[str] = []
        with open(self.transcripts, "rb") as f:
            transcripts = pickle.load(f)
            for text in transcripts:
                all_chunks.extend(self.chunk_text(text))
            logger.info("Total chunks after splitting: %d", len(all_chunks))

        # 2. Embed
        model = SentenceTransformer(self.EMBED_MODEL)
        embeddings = model.encode(all_chunks, show_progress_bar=True, normalize_embeddings=True)

        # 3. Build FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)   # inner-product works well with normalized embeddings
        index.add(embeddings)
        faiss.write_index(index, str(self.chunk_index))

        # 4. Save chunks so retrieval can map index → text
        Path(self.chunks_pkl).parent.mkdir(parents=True, exist_ok=True)
        with open(self.chunks_pkl, "wb") as f:
            pickle.dump(all_chunks, f)

        logger.info("Embedding completed. Index: %s  Chunks: %s", self.chunk_index, self.chunks_pkl)