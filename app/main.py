from fastapi import FastAPI
from config import settings
from routes import router
from db import Base, engine
from logging_setup import app_logger  
from metrics import metrics_middleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")


app.include_router(router)
app.middleware("http")(metrics_middleware)


@app.on_event("startup")
async def startup_event():
    app_logger.info(
        "startup",
        extra={"service": "auth-service", "instance": settings.instance_id}
    )


@app.on_event("shutdown")
async def shutdown_event():
    app_logger.info(
        "shutdown",
        extra={"service": "auth-service", "instance": settings.instance_id}
    )