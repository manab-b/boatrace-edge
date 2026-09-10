import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="BOAT RACE EDGE", version="0.1.0")


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    logger.warning("validation error path=%s detail=%s", request.url.path, exc)
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>BOAT RACE EDGE</title></head><body><main><h1>BOAT RACE EDGE</h1><p>Foundation is running. No prediction signals are generated at this phase.</p></main></body></html>"""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
