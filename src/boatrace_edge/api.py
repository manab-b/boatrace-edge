from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .domain import SettlementStatus
from .integrity import validate_observation_cutoff

app = FastAPI(title="BOAT RACE EDGE", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>BOAT RACE EDGE</title></head><body><main><h1>BOAT RACE EDGE</h1><p>Foundation is running. No prediction signals are generated at this phase.</p></main></body></html>"""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/integrity/example")
def integrity_example() -> dict[str, str]:
    return {"refund_status": SettlementStatus.REFUND.value}
