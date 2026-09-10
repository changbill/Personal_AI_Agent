"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    application = FastAPI(title="Personal AI Agent")
    application.include_router(chat_router)
    return application


app = create_app()
