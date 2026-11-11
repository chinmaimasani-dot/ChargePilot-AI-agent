"""Retriever tests with fakes: role isolation, top-k, empty-evidence rule."""

from app.rag.config import RAGSettings
from app.rag.retriever import KnowledgeRetriever


class FakeEmbedder:
    def embed_documents(self, texts):
        return [[1.0] * 4 for _ in texts]

    def embed_query(self, text):
        return [1.0] * 4


class FakeSearch:
    def __init__(self):
        self.last_call = None

    def __call__(self, query_embedding, *, audience, top_k, min_score):
        self.last_call = {
            "audience": audience,
            "top_k": top_k,
            "min_score": min_score,
        }
        return [
            {
                "document_id": "d1",
                "chunk_index": 0,
                "content": "chunk",
                "title": "T",
                "score": 0.9,
            }
        ]


def test_retriever_filters_by_trusted_audience():
    search = FakeSearch()
    retriever = KnowledgeRetriever(
        embedder=FakeEmbedder(),
        search=search,
        settings=RAGSettings(top_k=2, min_score=0.5),
    )
    results = retriever.retrieve("What is CCS2?", audience="driver")
    assert search.last_call == {"audience": "driver", "top_k": 2, "min_score": 0.5}
    assert len(results) == 1
    assert results[0]["title"] == "T"


def test_retriever_empty_question_returns_nothing():
    retriever = KnowledgeRetriever(embedder=FakeEmbedder(), search=FakeSearch())
    assert retriever.retrieve("   ", audience="owner") == []


def test_retriever_min_score_filters_weak_evidence():
    def weak_search(query_embedding, *, audience, top_k, min_score):
        return [
            {
                "document_id": "d1",
                "chunk_index": 0,
                "content": "weak",
                "title": "T",
                "score": 0.2,
            }
        ]

    retriever = KnowledgeRetriever(
        embedder=FakeEmbedder(),
        search=weak_search,
        settings=RAGSettings(min_score=0.75),
    )
    assert retriever.retrieve("random question", audience="owner") == []
