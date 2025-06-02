from typing import Optional, Dict, List
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document


def load_vectorstore(persist_directory: str, model_name: str = "BAAI/bge-base-en-v1.5") -> Chroma:

    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    return Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )

def chunk_retriever(
    vectorstore: Chroma,
    query: str,
    k: int = 5,
    metadata_filter: Optional[Dict] = None
) -> List[Document]:

    search_kwargs = {"k": k}
    if metadata_filter:
        search_kwargs["filter"] = metadata_filter

    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
    return retriever.get_relevant_documents(query)








