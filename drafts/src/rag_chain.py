from typing import Dict
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.llms import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer

from rag_pipeline.retriever import chunk_retriever

# # Example usage for chaining
# vectorstore = load_vectorstore("data/chroma_store")
# docs = chunk_retriever(vectorstore, query="AI chip outlook", k=5)

# # For RAG: return text chunks and metadata
# rag_inputs = [{"text": doc.page_content, "metadata": doc.metadata} for doc in docs]
# for item in rag_inputs:
#     print(item)

# def format_docs(docs):
#     return "\n\n".join(doc.page_content for doc in docs)

class FinancialNewsRAG:
    def __init__(
        self,
        chroma_path: str = "data/chroma_store",
        embedding_model: str = "BAAI/bge-base-en-v1.5",
        llm_model: str = "tiiuae/falcon-rw-1b",
        top_k: int = 5,
    ):
        self.chroma_path = chroma_path
        self.embedding_model = embedding_model
        self.top_k = top_k

        model = AutoModelForCausalLM.from_pretrained(llm_model)
        tokenizer = AutoTokenizer.from_pretrained(llm_model)

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        hf_pipeline = HuggingFacePipeline(
            task="text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
        )

        self.llm = HuggingFacePipeline(pipeline=hf_pipeline)

        self.prompt_template = PromptTemplate.from_template(
            """You are a financial news expert assistant. Use the following context to answer the question.
            
            Context:
            {context}
            
            Question: {question}
            
            Answer:"""
        )

        self.chain = (
            {
                "context": lambda q: format_docs(
                    chunk_retriever(self.chroma_path, self.embedding_model, q, self.top_k)
                ),
                "question": RunnablePassthrough(),
            }
            | self.prompt_template
            | self.llm
        )

    def answer_question(self, question: str) -> Dict:
        docs = chunk_retriever(self.chroma_path, self.embedding_model, question, self.top_k)
        result = self.chain.invoke(question)

        return {
            "answer": result,
            "sources": [{"text": doc.page_content, "metadata": doc.metadata} for doc in docs]
        }
