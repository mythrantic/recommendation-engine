from typing import Union, Optional
import debugpy
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI, Query, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
import httpx
import os

load_dotenv()
app = FastAPI()
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

debugpy.listen(("0.0.0.0", 5678))

@app.get("/")
def read_root():
    return {"Hello": "World ass wiper"}

@app.get("/api/manga")
async def recomend_manga(title: str = Query(..., example="Apocalyptic Thief"), size: Optional[int] = 1):
    search_results = await recomend_mangas(title=title, size=size)
    return search_results


@app.get("/api/movies")
async def recomend_movie(title: str = Query(..., example="Rogue One: A Star Wars Story (2016)"), size: Optional[int] = 1):
    search_results = await recomend_movies(title=title, size=size)
    return search_results

Instrumentator().instrument(app).expose(app)