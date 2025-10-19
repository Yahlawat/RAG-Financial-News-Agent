from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

def get_retriever(persist_path: str = "data/chroma_store", model_name: str = "BAAI/bge-base-en-v1.5", k: int = 5):
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    vectorstore = Chroma(persist_directory=persist_path, embedding_function=embedding_model)
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
        )
