import time

from fastapi import FastAPI, Request

from .db import Base, engine
from .routes import router
from .metrics import http_requests_total, http_request_duration

Base.metadata.create_all(bind=engine)

app = FastAPI(title="auth-service")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    path = request.url.path
    http_requests_total.labels(
        method=request.method, path=path, status=response.status_code
    ).inc()
    http_request_duration.labels(method=request.method, path=path).observe(duration)
    return response


app.include_router(router)
