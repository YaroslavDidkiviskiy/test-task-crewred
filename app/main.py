from fastapi import FastAPI
from app.core.db import init_db
from app.routes import api_router

def create_app() -> FastAPI:
    app = FastAPI(title="Travel Planner API")
    app.include_router(api_router)
    return app

app = create_app()

@app.on_event("startup")
def on_startup():
    init_db()
