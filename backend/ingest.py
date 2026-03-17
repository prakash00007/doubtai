"""
DoubtAI — Book Ingestion
==========================
Run ONCE per book to load it into Pinecone.

Usage:
    python ingest.py                     # all books in /books folder
    python ingest.py --book physics11    # one specific book
    python ingest.py --list              # see all available books
    python ingest.py --test              # dry run, no Pinecone writes
"""
import os, sys, argparse
from dotenv import load_dotenv
load_dotenv()

BOOKS = {
    "physics11":   {"file": "books/ncert_physics_11.pdf",   "name": "NCERT Physics 11",   "subject": "Physics"},
    "physics12":   {"file": "books/ncert_physics_12.pdf",   "name": "NCERT Physics 12",   "subject": "Physics"},
    "chemistry11": {"file": "books/ncert_chemistry_11.pdf", "name": "NCERT Chemistry 11", "subject": "Chemistry"},
    "chemistry12": {"file": "books/ncert_chemistry_12.pdf", "name": "NCERT Chemistry 12", "subject": "Chemistry"},
    "biology11":   {"file": "books/ncert_biology_11.pdf",   "name": "NCERT Biology 11",   "subject": "Biology"},
    "biology12":   {"file": "books/ncert_biology_12.pdf",   "name": "NCERT Biology 12",   "subject": "Biology"},
    "maths11":     {"file": "books/ncert_maths_11.pdf",     "name": "NCERT Maths 11",     "subject": "Maths"},
    "maths12":     {"file": "books/ncert_maths_12.pdf",     "name": "NCERT Maths 12",     "subject": "Maths"},
    "hcv1":          {"file": "books/hcv_vol1.pdf",                    "name": "HC Verma Vol 1",                    "subject": "Physics"},
    "hcv2":          {"file": "books/hcv_vol2.pdf",                    "name": "HC Verma Vol 2",                    "subject": "Physics"},
    "hcv_sol":       {"file": "books/hcv_solutions.pdf",               "name": "HC Verma Solutions",                "subject": "Physics"},
    "chemistry11":   {"file": "books/ncert_chemistry_11.pdf",          "name": "NCERT Chemistry 11",                "subject": "Chemistry"},
    "biology11":     {"file": "books/ncert_biology_11.pdf",            "name": "NCERT Biology 11",                  "subject": "Biology"},
    "biology12":     {"file": "books/ncert_biology_12.pdf",            "name": "NCERT Biology 12",                  "subject": "Biology"},
    "black_book":    {"file": "books/black_book_maths.pdf",            "name": "Black Book Maths by Vikas Gupta",   "subject": "Maths"},
    "exemplar_che12":{"file": "books/ncert_exemplar_chemistry_12.pdf", "name": "NCERT Exemplar Chemistry 12",       "subject": "Chemistry"},
}


def check_env():
    key = os.getenv("PINECONE_API_KEY", "")
    if not key or "your" in key:
        print("\n❌ PINECONE_API_KEY missing in .env file")
        print("   Add it and try again.\n")
        sys.exit(1)
    print("✅ API keys found\n")


def process(book: dict, dry_run=False) -> int:
    from utils.pdf_parser import extract_text, chunk_text
    from utils.embedder import embed_batch
    from utils.vector_store import store_chunks

    print(f"\n{'='*50}")
    print(f"  {book['name']}")
    print(f"{'='*50}")

    print("\n[1/3] Reading PDF...")
    try:
        text = extract_text(book["file"])
    except FileNotFoundError as e:
        print(e)
        return 0

    print("\n[2/3] Splitting into chunks...")
    chunks = chunk_text(text)
    print(f"   → {len(chunks)} chunks")

    if dry_run:
        print("\n🧪 DRY RUN — not writing to Pinecone")
        print(f"   Sample: {chunks[0]['text'][:150]}...")
        return 0

    print(f"\n[3/3] Embedding + storing {len(chunks)} chunks...")
    embeddings = embed_batch([c["text"] for c in chunks])
    stored = store_chunks(chunks, book["name"], book["subject"], embeddings)
    print(f"\n✅ Stored {stored} chunks for '{book['name']}'")
    return stored


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", help="e.g. physics11")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable books:")
        for k, b in BOOKS.items():
            found = "✅" if os.path.exists(b["file"]) else "❌ not found"
            print(f"  --book {k:15} {b['name']} [{found}]")
        print()
        return

    check_env()

    if args.book:
        if args.book not in BOOKS:
            print(f"❌ Unknown: {args.book}. Run --list to see options.")
            sys.exit(1)
        to_process = [BOOKS[args.book]]
    else:
        to_process = [b for b in BOOKS.values() if os.path.exists(b["file"])]
        missing = [b for b in BOOKS.values() if not os.path.exists(b["file"])]
        if missing:
            print(f"⚠️  {len(missing)} book(s) not found in /books (skipping):")
            for b in missing:
                print(f"   ❌ {b['file']}")
            print()

    if not to_process:
        print("❌ No books found. Download PDFs to backend/books/")
        print("   https://ncert.nic.in/textbook.php\n")
        return

    total = sum(process(b, args.test) for b in to_process)

    print(f"\n{'='*50}")
    print(f"🎉 Done! {len(to_process)} books, {total:,} chunks stored")
    print(f"\nNext → python server.py")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()