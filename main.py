from typing import List

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config_logic import effective_config

app = FastAPI(title="Layered config")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/effective-config")
def get_effective_config(set_: List[str] = Query(default=[], alias="set")):
    try:
        return effective_config(set_)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
