import time
from fastapi import Request
from prometheus_client import Counter, Histogram

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
    ["result"],
)


EXCLUDED_PATHS = {"/healthz", "/metrics"}


async def metrics_middleware(request: Request, call_next):
    """Middleware для сбора метрик HTTP-запросов."""
    start_time = time.time()
    
    response = await call_next(request)
    duration = time.time() - start_time
    
    path = request.url.path
    
    
    if path in EXCLUDED_PATHS:
        return response
    
    http_requests_total.labels(
        method=request.method,
        path=path,
        status=response.status_code
    ).inc()
    
    http_request_duration.labels(
        method=request.method,
        path=path
    ).observe(duration)
    
    if path == "/login":
        result = "success" if response.status_code == 200 else "failed"
        login_attempts_total.labels(result=result).inc()
    
    return response