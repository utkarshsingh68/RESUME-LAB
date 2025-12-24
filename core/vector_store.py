"""FAISS-based semantic search for resume matching."""
import numpy as np
import faiss
import pickle
from typing import List, Tuple, Dict
from pathlib import Path
from config import settings


class VectorStore:
    """Production-grade FAISS vector store for semantic search."""
    
    def __init__(self, dimension: int = None):
        """Initialize FAISS index."""
        self.dimension = dimension or settings.FAISS_DIMENSION
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []  # Store chunk metadata
        self.embeddings_map = {}
    
    def add_vectors(self, embeddings: np.ndarray, metadata: List[Dict]) -> None:
        """Add embeddings and metadata to index."""
        if embeddings.shape[0] != len(metadata):
            raise ValueError("Number of embeddings must match metadata length")
        
        # Normalize embeddings for better search
        embeddings = self._normalize(embeddings)
        self.index.add(embeddings)
        self.metadata.extend(metadata)
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[float, Dict]]:
        """Search for k nearest neighbors."""
        query_embedding = self._normalize(query_embedding.reshape(1, -1))
        distances, indices = self.index.search(query_embedding, min(k, len(self.metadata)))
        
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.metadata):
                # Convert L2 distance to similarity score
                distance_val = float(distance)
                similarity = 1 / (1 + distance_val)
                results.append((float(similarity), self.metadata[idx]))
        
        return results
    
    def save(self, path: str = None) -> None:
        """Persist index and metadata to disk."""
        path = path or settings.FAISS_INDEX_PATH
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, path)
        with open(f"{path}.metadata", "wb") as f:
            pickle.dump(self.metadata, f)
    
    def load(self, path: str = None) -> None:
        """Load index and metadata from disk."""
        path = path or settings.FAISS_INDEX_PATH
        
        if Path(path).exists():
            self.index = faiss.read_index(path)
            with open(f"{path}.metadata", "rb") as f:
                self.metadata = pickle.load(f)
    
    @staticmethod
    def _normalize(embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings for cosine similarity via L2."""
        return embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)


class EmbeddingService:
    """Generate embeddings for resume chunks and queries."""
    
    def __init__(self):
        """Initialize embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight, production-ready
        except ImportError:
            raise ImportError("Install sentence-transformers: pip install sentence-transformers")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for single text."""
        return self.model.encode(text, convert_to_numpy=True).astype('float32')
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for batch of texts."""
        return self.model.encode(texts, convert_to_numpy=True).astype('float32')
