import os

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.llms import Ollama

from retriever import load_vectorstore, chunk_retriever


def format_docs(docs: list) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def rag_chain(question: str, top_k: int = 5) -> dict:
    vectorstore_path = "data/chroma_store"
    vectorstore = load_vectorstore(vectorstore_path)

    def retrieve_context(query: str) -> str:
        relevant_docs = chunk_retriever(vectorstore, query=query, k=top_k)
        return format_docs(relevant_docs)

    prompt_template = PromptTemplate.from_template(
        """You are a financial news expert assistant. Use the following context to answer the question.

        Context:
        {context}

        Question: {question}

        Answer:"""
    )

    llm = Ollama(
        model="llama3.2:3b", 
        temperature=0.0,
        system="You are a helpful assistant for financial news question answering."
    )

    chain = (
        {
            "context": RunnablePassthrough() | (lambda q_for_context: retrieve_context(q_for_context)),
            "question": RunnablePassthrough(),
        }
        | prompt_template
        | llm
    )

    answer_output = chain.invoke(question)

    source_docs = chunk_retriever(vectorstore, query=question, k=top_k)
    sources = [{"text": doc.page_content, "metadata": doc.metadata} for doc in source_docs]

    return {
        "answer": answer_output.strip(),
        "sources": sources
    }


# Example usage
if __name__ == "__main__":
    question = "How is Amazon doing in the current market?"
    try:
        result = rag_chain(question=question, top_k=5)

        print("## AI Generated Answer:")
        print(result["answer"])
        print("\n## Sources:")
        for i, source_doc in enumerate(result["sources"]):
            print(f"\n### Source {i+1}:")
            print(f"Text: \"{source_doc['text'][:200]}...\"")
            print(f"Metadata: {source_doc['metadata']}")
    except Exception as e:
        print(f"An error occurred: {e}")
