import logging

from finnews.common.logging import get_logger, setup_logging
from finnews.rag.embedder import main as embedder_main

logger = get_logger(__name__)


def main() -> int:
    """
    CLI entry point for the embedding step.

    Reads processed chunks from data/processed_chunks/ and generates
    embeddings, storing them in the ChromaDB vector store at data/chroma_store/.
    """
    setup_logging(component="rag", level=logging.INFO, console=True)

    try:
        embedder_main()
        return 0
    except Exception as e:
        logger.error(f"Error during embedding: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
