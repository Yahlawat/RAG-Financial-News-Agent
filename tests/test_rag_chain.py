import sys
import types
import importlib
from datetime import datetime
from pathlib import Path

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def import_rag_chain(monkeypatch):
    class Document:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}

    # stub modules needed at import
    chroma_mod = types.ModuleType('langchain_chroma')
    chroma_mod.Chroma = object
    prompt_mod = types.ModuleType('langchain_core.prompts')
    class DummyPrompt:
        @classmethod
        def from_template(cls, template):
            class P:
                def __ror__(self, other):
                    return other
            return P()
    prompt_mod.PromptTemplate = DummyPrompt

    runnable_mod = types.ModuleType('langchain_core.runnables')
    class DummyPassthrough:
        def __or__(self, other):
            return lambda x: other(x)
    runnable_mod.RunnablePassthrough = DummyPassthrough

    llm_mod = types.ModuleType('langchain_ollama')
    class DummyLLM:
        def __init__(self, *a, **k):
            pass
        def __ror__(self, other):
            class C:
                def invoke(self_inner, q):
                    return 'dummy answer'
            return C()
    llm_mod.OllamaLLM = DummyLLM

    monkeypatch.setitem(sys.modules, 'langchain_chroma', chroma_mod)
    monkeypatch.setitem(sys.modules, 'langchain_core.prompts', prompt_mod)
    monkeypatch.setitem(sys.modules, 'langchain_core.runnables', runnable_mod)
    monkeypatch.setitem(sys.modules, 'langchain_ollama', llm_mod)

    # patch retriever functions
    class DummyStore:
        pass

    def fake_article_chunk_retriever(store, query, target_tickers=None, top_n=5):
        return [Document('article', {'title':'T','url':'U','published_date': '2024-01-01'})]

    def fake_retrieve_chat_memory(store, conversation_id, query, k=3):
        return [Document('history', {})]

    def fake_add_chat_memory(store, conversation_id, user_id, question, answer, model_name='x'):
        pass

    retr_mod = types.ModuleType('rag_pipeline.retriever')
    retr_mod.load_vectorstore = lambda path, model_name='x': DummyStore()
    retr_mod.article_chunk_retriever = fake_article_chunk_retriever
    retr_mod.retrieve_chat_memory = fake_retrieve_chat_memory
    retr_mod.add_chat_memory = fake_add_chat_memory
    sys.modules['rag_pipeline.retriever'] = retr_mod
    schema_mod = types.ModuleType('langchain.schema')
    schema_mod.Document = Document
    monkeypatch.setitem(sys.modules, 'langchain.schema', schema_mod)

    if 'rag_pipeline.rag_chain' in sys.modules:
        del sys.modules['rag_pipeline.rag_chain']
    return importlib.import_module('rag_pipeline.rag_chain'), Document, DummyStore


def test_rag_chat_answer_generation(monkeypatch):
    rag_chain, Document, DummyStore = import_rag_chain(monkeypatch)

    result = rag_chain.rag_chat('question', conversation_id='1', user_id='u', article_store=DummyStore(), chat_store=DummyStore())
    assert result['answer'] == 'dummy answer'
    assert result['conversation_id'] == '1'
    assert result['sources'][0]['title'] == 'T'
