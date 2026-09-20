from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalMetrics:
    precision: float
    recall: float


def retrieval_metrics(retrieved: list[str], expected: list[str]) -> RetrievalMetrics:
    if not retrieved:
        return RetrievalMetrics(precision=0.0, recall=0.0 if expected else 1.0)
    relevant = sum(
        1 for passage in retrieved if any(marker.lower() in passage.lower() for marker in expected)
    )
    found = sum(
        1 for marker in expected if any(marker.lower() in passage.lower() for passage in retrieved)
    )
    return RetrievalMetrics(
        precision=relevant / len(retrieved),
        recall=found / len(expected) if expected else 1.0,
    )


def citations_are_correct(answer: str, citations: list[str]) -> bool:
    return bool(citations) and all(
        any(sentence.strip() in citation for citation in citations)
        for sentence in answer.split(". ")
        if sentence.strip()
    )


def answer_is_grounded(answer: str, source_texts: list[str]) -> bool:
    joined_sources = " ".join(source_texts)
    return all(
        sentence.strip().rstrip(".") in joined_sources
        for sentence in answer.split(". ")
        if sentence.strip()
    )
