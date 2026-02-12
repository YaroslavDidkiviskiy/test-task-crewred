from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.db import init_db
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (якщо потрібно)


def create_app() -> FastAPI:
    app = FastAPI(title="Travel Planner API", lifespan=lifespan)
    app.include_router(api_router)
    return app


app = create_app()
