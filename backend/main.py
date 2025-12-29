import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.config import load_settings
from app.db import Database
from .routes import router

APP_PORT = int(os.getenv("BACKEND_PORT", "8011"))

app = FastAPI(title="NY Bot Admin Backend", version="0.1.0")
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    settings = load_settings()
    app.state.db = await Database.create(settings.db_path)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    db: Database | None = getattr(app.state, "db", None)
    if db:
        await db.close()


@app.get("/health")
async def health() -> JSONResponse:
    db_status = "ok" if getattr(app.state, "db", None) else "not_ready"
    return JSONResponse({"status": "ok", "db": db_status})


def run() -> None:
    # Convenience entrypoint for `python -m backend.main`
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=APP_PORT,
        reload=bool(int(os.getenv("BACKEND_RELOAD", "0"))),
    )


if __name__ == "__main__":
    run()

