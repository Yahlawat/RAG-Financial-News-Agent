from rag_pipeline.rag_chain import FinancialNewsRAG

def main():
    print("Financial News RAG Assistant")
    print("Loading models and initializing system...")
    
    try:
        rag = FinancialNewsRAG()
        print("System ready!")
    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        return

    while True:
        question = input("\nEnter your question (or 'exit' to quit): ")
        if question.lower() == "exit":
            break

        try:
            result = rag.answer_question(question)
            print("\nAnswer:", result["answer"])
            print("\nSources:")
            for i, src in enumerate(result["sources"], 1):
                title = src['metadata'].get('title', 'Unknown Title')
                url = src['metadata'].get('url', 'No URL')
                print(f"{i}. {title}")
                if url != 'No URL':
                    print(f"   URL: {url}")
                print(f"   Preview: {src['text'][:100]}...")
        except Exception as e:
            print(f"Error processing question: {e}")

if __name__ == "__main__":
    main()