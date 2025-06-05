import uuid
import sys

from rag_pipeline.rag_chain import rag_chat


def run_chat_session():
    
    raw = input("Enter comma-separated tickers to filter by (or press Enter for no filter): ").strip()
    if raw:
        tickers_to_filter = [t.strip().upper() for t in raw.split(",") if t.strip()]
    else:
        tickers_to_filter = None
        
    conversation_id = str(uuid.uuid4())
    print("Starting new chat session. (Type 'exit' or 'quit' to end)\n")

    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in ["exit", "quit"]:
            print("Ending chat. Goodbye!")
            break

        try:
            response = rag_chat(
                question=question,
                conversation_id=conversation_id,
                target_tickers=tickers_to_filter,
                top_k=5,
                chat_k=3
            )
        except Exception as e:
            print(f"An error occurred while generating response: {e}")
            continue

        print(f"\nAssistant: {response['answer']}\n")

        if response.get("sources"):
            print("Sources:")
            seen_urls = set()
            for src in response["sources"]:
                url = src.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                title = src.get("title", "(no title)")
                published_date = src.get("published_date", "(no date)")
                print(f"  • {title} — {url} ({published_date})")
            print("")


if __name__ == "__main__":
    try:
        run_chat_session()
    except KeyboardInterrupt:
        print("\nChat interrupted. Goodbye!")
        sys.exit(0)
