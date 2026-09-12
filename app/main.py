"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.core.logging import configure_logging
from app.services.runtime import close_runtime


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Close the calendar MCP session on shutdown so no server process is orphaned."""
    yield
    close_runtime()


def create_app() -> FastAPI:
    configure_logging()
    application = FastAPI(title="Personal AI Agent", lifespan=lifespan)
    web_directory = Path(__file__).parent / "web"
    application.mount("/static", StaticFiles(directory=web_directory), name="static")

    @application.get("/", include_in_schema=False)
    def chat_page() -> FileResponse:
        return FileResponse(web_directory / "index.html")

    application.include_router(chat_router)
    return application


app = create_app()
