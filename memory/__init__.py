"""Memory layer for Unagi - SQLite database and vector store."""
from .database import Database
from .vector_store import VectorStore
from .embeddings import generate_embedding, embed_log
from .retrieval import get_relevant_context

__all__ = [
    'Database',
    'VectorStore',
    'generate_embedding',
    'embed_log',
    'get_relevant_context'
]

# Made with Bob
