"""
Pause AI Student Wellness Companion — Embedding & Retrieval Service
Uses candidate sentence-transformers/all-MiniLM-L6-v2 (pinned to revision 8b3219a92973c328a8e22fadcfa821b5dc75636a).
Strictly tenant-scoped, English only, with chunking for long entries and relevance thresholding.
"""

import json
import re
from typing import List, Dict, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "8b3219a92973c328a8e22fadcfa821b5dc75636a"

# Relevance threshold for semantic search: scores below this will not be forced into top-k
RELEVANCE_THRESHOLD = 0.38

class EmbeddingService:
    def __init__(self):
        self.model_id = MODEL_ID
        self.model_version = MODEL_REVISION
        self._model: Optional[SentenceTransformer] = None

    def _load_model(self):
        if self._model is None:
            self._model = SentenceTransformer(
                MODEL_ID,
                revision=MODEL_REVISION
            )

    def chunk_text(self, text: str, max_words: int = 150, overlap_words: int = 30) -> List[str]:
        """
        Chunk longer entries to avoid the 256 word-piece truncation boundary
        documented in the all-MiniLM-L6-v2 model card.
        Short entries are returned as a single chunk.
        """
        words = text.strip().split()
        if len(words) <= max_words:
            return [text.strip()]
        
        chunks = []
        step = max_words - overlap_words
        for i in range(0, len(words), step):
            chunk = " ".join(words[i : i + max_words])
            chunks.append(chunk)
            if i + max_words >= len(words):
                break
        return chunks

    def embed_text(self, text: str) -> List[float]:
        """Generate a 384-dimensional vector embedding for text."""
        self._load_model()
        # Clean text
        cleaned = text.strip()
        if not cleaned:
            return [0.0] * 384
        
        # If text is long, average chunk embeddings
        chunks = self.chunk_text(cleaned)
        embeddings = self._model.encode(chunks, normalize_embeddings=True)
        if len(chunks) == 1:
            return embeddings[0].tolist()
        else:
            mean_emb = np.mean(embeddings, axis=0)
            norm = np.linalg.norm(mean_emb)
            if norm > 0:
                mean_emb = mean_emb / norm
            return mean_emb.tolist()

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute exact cosine similarity between two unit-normalized vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    @staticmethod
    def lexical_keyword_score(query: str, document: str) -> float:
        """Compute simple token-overlap score between query terms and document text."""
        q_tokens = set(re.findall(r'\w+', query.lower()))
        d_tokens = set(re.findall(r'\w+', document.lower()))
        
        # Ignore common non-informative words
        stopwords = {"the", "a", "an", "is", "in", "it", "to", "and", "of", "for", "on", "what", "did", "i", "say", "when", "my"}
        q_clean = q_tokens - stopwords
        if not q_clean:
            return 0.0
        
        overlap = len(q_clean.intersection(d_tokens))
        return float(overlap / len(q_clean))

# Global singleton
embedding_service = EmbeddingService()
