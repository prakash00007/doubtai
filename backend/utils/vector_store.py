"""
All Pinecone read/write operations — updated for pinecone-client v6
"""
import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from utils.embedder import EMBEDDING_DIM

load_dotenv()

INDEX_NAME = os.getenv("PINECONE_INDEX", "doubtai")
_index = None


def _get_index():
    global _index
    if _index is None:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

        # Create index if it doesn't exist
        existing = [i.name for i in pc.list_indexes()]
        if INDEX_NAME not in existing:
            print(f"🗄️  Creating Pinecone index '{INDEX_NAME}'...")
            pc.create_index(
                name=INDEX_NAME,
                dimension=EMBEDDING_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            print("   ✅ Index created\n")

        _index = pc.Index(INDEX_NAME)
    return _index


def store_chunks(chunks: list, book_name: str, subject: str, embeddings: list) -> int:
    index = _get_index()
    BATCH = 100
    total = 0

    for i in range(0, len(chunks), BATCH):
        bc = chunks[i:i+BATCH]
        be = embeddings[i:i+BATCH]
        vectors = []
        for chunk, emb in zip(bc, be):
            vid = f"{book_name.replace(' ','_')}_{chunk['index']}"
            vectors.append({
                "id":     vid,
                "values": emb,
                "metadata": {
                    "text":      chunk["text"],
                    "book":      book_name,
                    "subject":   subject,
                    "chunk_idx": chunk["index"]
                }
            })
        index.upsert(vectors=vectors)
        total += len(vectors)
        pct = min((i + BATCH) / len(chunks) * 100, 100)
        print(f"   [{pct:.0f}%] {total}/{len(chunks)} stored...")

    return total


def search(query_vector: list, subject: str = None, top_k: int = 5) -> list:
    index = _get_index()
    query_filter = {"subject": {"$eq": subject}} if subject and subject != "All" else {}
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        filter=query_filter if query_filter else None
    )
    return [
        {
            "text":    m.metadata.get("text", ""),
            "book":    m.metadata.get("book", "Unknown"),
            "subject": m.metadata.get("subject", ""),
            "score":   round(m.score, 3)
        }
        for m in results.matches
    ]


def get_stats() -> dict:
    index = _get_index()
    stats = index.describe_index_stats()
    return {"total_vectors": stats.total_vector_count, "index": INDEX_NAME}


if __name__ == "__main__":
    print(get_stats())