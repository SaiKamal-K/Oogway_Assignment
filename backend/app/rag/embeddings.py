import logging
from typing import List, Union
import numpy as np
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_model = None

def get_embedding_model():
    """Lazily load the SentenceTransformer model to optimize startup time."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
            try:
                # Fast path: load from local cache if already downloaded
                _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, local_files_only=True)
            except Exception:
                _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        except Exception as e:
            logger.warning(f"SentenceTransformer not available or failed to load ({e}). Using deterministic fallback.")
            _model = "fallback"
    return _model

def compute_embedding(text: str) -> List[float]:
    """Compute a 384-dimensional vector embedding for the given text."""
    model = get_embedding_model()
    if model != "fallback":
        try:
            vector = model.encode(text, normalize_embeddings=True)
            return vector.tolist()
        except Exception as e:
            logger.error(f"Error computing embedding: {e}. Falling back.")

    # Deterministic fallback embedding for testing/minimal environments (384 dimensions)
    np.random.seed(abs(hash(text)) % (2**32))
    vec = np.random.randn(settings.EMBEDDING_DIMENSION).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()

def compute_batch_embeddings(texts: List[str]) -> List[List[float]]:
    """Compute vector embeddings in batch."""
    model = get_embedding_model()
    if model != "fallback":
        try:
            vectors = model.encode(texts, normalize_embeddings=True, batch_size=32)
            return [v.tolist() for v in vectors]
        except Exception as e:
            logger.error(f"Error computing batch embeddings: {e}")

    return [compute_embedding(t) for t in texts]
