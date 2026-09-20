import json
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.database.models import User
from app.evaluation import answer_is_grounded, citations_are_correct, retrieval_metrics
from app.generation.providers import ExtractiveGenerationProvider
from app.retrieval.embeddings import LocalHashEmbeddingProvider
from app.retrieval.search import hybrid_search
from tests.test_retrieval import add_ready_document


def test_fixed_retrieval_and_answer_quality_dataset(db: Session) -> None:
    dataset = json.loads((Path(__file__).parent / "fixtures" / "evaluation.json").read_text())
    owner = User(email="evaluation@example.com", password_hash="unused")
    db.add(owner)
    db.flush()
    for document in dataset["documents"]:
        add_ready_document(db, owner, document["name"], document["passages"])

    embedding_provider = LocalHashEmbeddingProvider()
    generator = ExtractiveGenerationProvider()
    factual_precisions: list[float] = []
    factual_recalls: list[float] = []
    latencies: list[float] = []
    failures = 0
    for case in dataset["questions"]:
        started = time.perf_counter()
        results = hybrid_search(
            db,
            embedding_provider,
            owner.id,
            case["question"],
            [],
            None,
            None,
            3,
        )
        answer = generator.generate(case["question"], results)
        latencies.append((time.perf_counter() - started) * 1000)
        if answer.supported != case["expect_supported"]:
            failures += 1
        if case["expected_passages"]:
            metrics = retrieval_metrics(
                [result.content for result in results], case["expected_passages"]
            )
            factual_precisions.append(metrics.precision)
            factual_recalls.append(metrics.recall)
            citations = [results[index].content for index in answer.cited_result_indexes]
            assert citations_are_correct(answer.text, citations)
            assert answer_is_grounded(answer.text, citations)
        else:
            assert answer.cited_result_indexes == []

    assert sum(factual_recalls) / len(factual_recalls) == 1.0
    assert sum(factual_precisions) / len(factual_precisions) >= 0.5
    assert max(latencies) < 1000
    assert failures == 0


def test_metric_edge_cases() -> None:
    empty = retrieval_metrics([], [])
    assert empty.precision == 0
    assert empty.recall == 1
    assert not citations_are_correct("answer", [])
