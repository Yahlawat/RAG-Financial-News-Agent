from rag_pipeline.rag_chain import FinancialNewsRAG

if __name__ == "__main__":
    rag = FinancialNewsRAG(
        chroma_path="data/chroma_store",
        embedding_model="BAAI/bge-base-en-v1.5",
        llm_model="tiiuae/falcon-rw-1b",
        top_k=5,
    )

    question = "What is the current outlook for Nvidia?"
    result = rag.answer_question(question)

    print("\n🧠 Answer:")
    print(result["answer"])

    print("\n📚 Sources:")
    for i, src in enumerate(result["sources"], 1):
        print(f"\nSource {i}:")
        print(f"Metadata: {src['metadata']}")
        print(f"Content: {src['text'][:300]}...")  # Truncate for readability
