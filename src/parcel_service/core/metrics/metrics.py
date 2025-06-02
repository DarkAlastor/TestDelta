from prometheus_client import Counter, Gauge, Histogram

HTTP_ERRORS = Counter(
    "http_request_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "status"]
)

REQUESTS_BY_CLIENT = Counter(
    "http_requests_by_client_total",
    "HTTP requests by client type",
    ["client_id"]
)

HTTP_RESPONSES = Counter(
    "http_response_total",
    "Total HTTP responses",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    name="http_requests_duration_seconds",
    documentation="Duration of HTTP requests in seconds",
    labelnames=["method", "path", "status"],
    buckets=[0.1, 0.3, 0.5, 1, 2, 5, 10]  # Настраивается под твои требования
)

IN_PROGRESS_REQUESTS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "path"]
)