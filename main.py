# main.py
from rag_pipeline.rag_chain import FinancialNewsRAG

def main():
    print("Financial News RAG Assistant")
    rag = FinancialNewsRAG()

    while True:
        question = input("\nComment on Nvida's recent performance. what is there to look forward to?")
        if question.lower() == "exit":
            break

        result = rag.answer_question(question)
        print("\nAnswer:", result["answer"])
        print("\nSources:")
        for src in result["sources"]:
            print(f"- {src['metadata'].get('title', '')} | {src['metadata'].get('url', '')}")

if __name__ == "__main__":
    main()