<<<<<<< HEAD
from finnews.rag.chunker import main as chunker_main


def main() -> int:
    """
    CLI entry point for the chunking step.

    Reads raw news articles from data/raw_news/ and splits them into
    chunks saved to data/processed_chunks/.
    """
    try:
        chunker_main()
        return 0
    except Exception as e:
        print(f"Error during chunking: {e}")
        return 1

=======
﻿def main() -> int:
    # TODO: wire to chunking step
    print("Chunk step placeholder")
    return 0
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d

if __name__ == "__main__":
    raise SystemExit(main())
