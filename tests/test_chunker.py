import sys
import types
import importlib
from pathlib import Path

import pytest

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def import_chunker(monkeypatch):
    class Document:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}

    class DummySplitter:
        def __init__(self, *args, **kwargs):
            pass
        def create_documents(self, texts, metadatas=None):
            docs = []
            for text, meta in zip(texts, metadatas or [{}]):
                for part in text.split('. '):
                    part = part.strip()
                    if part:
                        docs.append(Document(part, meta))
            return docs

    ts_mod = types.ModuleType('langchain.text_splitter')
    ts_mod.RecursiveCharacterTextSplitter = DummySplitter
    schema_mod = types.ModuleType('langchain.schema')
    schema_mod.Document = Document

    monkeypatch.setitem(sys.modules, 'langchain.text_splitter', ts_mod)
    monkeypatch.setitem(sys.modules, 'langchain.schema', schema_mod)

    if 'rag_pipeline.chunker' in sys.modules:
        del sys.modules['rag_pipeline.chunker']
    return importlib.import_module('rag_pipeline.chunker')


def test_chunk_articles_sentence_splitting(monkeypatch):
    chunker = import_chunker(monkeypatch)

    articles = [{
        'title': 'T',
        'url': 'u',
        'body': 'First sentence. Second sentence. Third sentence.'
    }]

    docs = chunker.chunk_articles(articles, max_characters=10)
    contents = [d.page_content for d in docs]
    assert len(contents) == 3
    assert contents[0].startswith('First')
