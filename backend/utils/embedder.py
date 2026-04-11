"""
FREE local embeddings — no API cost ever.
Downloads ~90MB model on first run, then cached forever..
"""
from sentence_transformers import SentenceTransformer

print("📦 Loading embedding model (first run downloads ~90MB)...")
_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embedding model ready\n")

EMBEDDING_DIM = 384


def embed_text(text: str) -> list:
    return _model.encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list) -> list:
    return _model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=64,
        show_progress_bar=True
    ).tolist()


if __name__ == "__main__":
    v = embed_text("What is Newton's second law?")
    print(f"✅ Vector dim: {len(v)}")
