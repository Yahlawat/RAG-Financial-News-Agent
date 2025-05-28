from typing import Dict
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from transformers.pipelines import pipeline
from transformers import AutoModelForCausalLM, AutoTokenizer

class FinancialNewsRAG:
    def __init__(
        self,
        chroma_path: str = "data/chroma_store",
        embedding_model: str = "BAAI/bge-base-en-v1.5",
        llm_model: str = "tiiuae/falcon-rw-1b",
        top_k: int = 5,
        offline: bool = True
    ):
        embedding = HuggingFaceEmbeddings(model_name=embedding_model)
        self.vectorstore = Chroma(persist_directory=chroma_path, embedding_function=embedding)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": top_k})

        if offline:
            model = AutoModelForCausalLM.from_pretrained(llm_model, local_files_only=True)
            tokenizer = AutoTokenizer.from_pretrained(llm_model, local_files_only=True)
        else:
            model = AutoModelForCausalLM.from_pretrained(llm_model)
            tokenizer = AutoTokenizer.from_pretrained(llm_model)

        hf_pipeline = pipeline(
            task="text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            do_sample=False,
            temperature=0  # Optional: you may remove if it's being ignored
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
            {"context": self.retriever, "question": RunnablePassthrough()}
            | self.prompt_template
            | self.llm
        )

    def answer_question(self, question: str) -> Dict:
        docs = self.retriever.invoke(question)
        context = "\n\n".join(doc.page_content for doc in docs)
        prompt = self.prompt_template.format(context=context, question=question)
        answer = self.llm.invoke(prompt)
        return {
            "answer": answer,
            "sources": [
                {"text": doc.page_content, "metadata": doc.metadata}
                for doc in docs
            ]
        }
