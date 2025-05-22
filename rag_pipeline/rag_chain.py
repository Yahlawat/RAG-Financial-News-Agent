from typing import List, Dict
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from retriever.embedder import NewsEmbedder

class FinancialNewsRAG:
    def __init__(self, openai_api_key: str):
        self.embedder = NewsEmbedder()
        self.llm = OpenAI(temperature=0, openai_api_key=openai_api_key)
        
        # Custom prompt template for financial news QA
        self.prompt_template = PromptTemplate(
            template="""You are a financial news expert assistant. Use the following pieces of context to answer the question at the end.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            
            Context:
            {context}
            
            Question: {question}
            
            Answer:""",
            input_variables=["context", "question"]
        )
        
        # Initialize the QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.embedder.collection.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt_template}
        )
    
    def answer_question(self, question: str) -> Dict:
        """
        Answer a question using the RAG pipeline.
        
        Args:
            question: The question to answer
            
        Returns:
            Dictionary containing the answer and source documents
        """
        result = self.qa_chain({"query": question})
        
        return {
            "answer": result["result"],
            "sources": [
                {
                    "text": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in result["source_documents"]
            ]
        } 