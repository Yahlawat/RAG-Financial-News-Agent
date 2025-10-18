import sys
import types
import importlib
from datetime import datetime
from pathlib import Path

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def import_retriever(monkeypatch):
    class Document:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}

    class DummyChroma:
        def __init__(self, docs=None):
            self.docs = docs or []
        def as_retriever(self, search_kwargs=None):
            docs = self.docs
            class R:
                def invoke(self, query):
                    return docs
            return R()

    ts_mod = types.ModuleType('langchain_chroma')
    ts_mod.Chroma = DummyChroma
    hf_mod = types.ModuleType('langchain_huggingface')
    hf_mod.HuggingFaceEmbeddings = lambda *a, **k: None
    schema_mod = types.ModuleType('langchain.schema')
    schema_mod.Document = Document

    monkeypatch.setitem(sys.modules, 'langchain_chroma', ts_mod)
    monkeypatch.setitem(sys.modules, 'langchain_huggingface', hf_mod)
    monkeypatch.setitem(sys.modules, 'langchain.schema', schema_mod)

    if 'finnews.rag.retriever' in sys.modules:
        del sys.modules['finnews.rag.retriever']
    return importlib.import_module('finnews.rag.retriever'), Document, DummyChroma


def test_article_chunk_retriever_top_k(monkeypatch):
    retriever, Document, DummyChroma = import_retriever(monkeypatch)

    now = datetime.now().isoformat()
    docs = [Document('doc'+str(i), {'published_date': now}) for i in range(3)]
    store = DummyChroma(docs)

    results = retriever.article_chunk_retriever(store, 'query', top_n=2)
    assert len(results) == 2
    assert all(isinstance(d, Document) for d in results)
