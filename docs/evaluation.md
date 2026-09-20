# Retrieval and answer-quality evaluation

The repository includes a fixed, versioned evaluation set at
`backend/tests/fixtures/evaluation.json`. It covers direct facts, questions that
require multiple passages, unsupported questions, and an instruction-override
attempt. Cross-user isolation is covered independently by API tests.

## Metrics and gates

The automated evaluation measures:

| Metric | Gate | Current deterministic baseline |
| --- | ---: | ---: |
| Retrieval recall | 100% | 100% |
| Retrieval precision | >= 50% | >= 50% |
| Citation correctness | 100% | 100% |
| Extractive groundedness | 100% | 100% |
| Local response latency | < 1,000 ms/case | Passing |
| Answer-behavior failure rate | 0% | 0% |

Run the evaluation with:

```bash
cd backend
pytest tests/test_evaluation.py tests/test_retrieval.py tests/test_question_answering.py
```

These numbers are a small regression baseline, not a claim of broad benchmark
quality. Before changing an embedding or generation provider, expand the fixture
with representative private-domain documents and compare results in CI.
