from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "document_search_http_requests_total",
    "HTTP requests handled",
    ["method", "path", "status"],
)
HTTP_LATENCY = Histogram(
    "document_search_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "path"],
)
INGESTION_JOBS = Counter(
    "document_search_ingestion_jobs_total",
    "Document ingestion job outcomes",
    ["outcome"],
)
SEARCH_LATENCY = Histogram(
    "document_search_retrieval_duration_seconds", "Hybrid retrieval duration"
)
GENERATION_LATENCY = Histogram(
    "document_search_generation_duration_seconds", "Answer generation duration"
)
CACHE_OPERATIONS = Counter(
    "document_search_cache_operations_total", "Search cache outcomes", ["outcome"]
)
QUEUE_DEPTH = Gauge("document_search_ingestion_queue_depth", "Pending ingestion jobs")
