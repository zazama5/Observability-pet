from prometheus_client import Counter, Histogram

# Метрики, которые Prometheus снимает с /metrics.
# ServiceMonitor (kube-prometheus-stack) скрейпит этот эндпоинт.

http_requests_total = Counter(
    "auth_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

http_request_duration = Histogram(
    "auth_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)

login_attempts_total = Counter(
    "auth_login_attempts_total",
    "Login attempts",
    ["result"],  # success | failed
)
