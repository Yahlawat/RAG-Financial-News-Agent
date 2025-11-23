<<<<<<< HEAD
from finnews.rag.embedder import main as embedder_main


def main() -> int:
    """
    CLI entry point for the embedding step.

    Reads processed chunks from data/processed_chunks/ and generates
    embeddings, storing them in the ChromaDB vector store at data/chroma_store/.
    """
    try:
        embedder_main()
        return 0
    except Exception as e:
        print(f"Error during embedding: {e}")
        return 1

=======
﻿def main() -> int:
    # TODO: wire to embedding step
    print("Embed step placeholder")
    return 0
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d

if __name__ == "__main__":
    raise SystemExit(main())
