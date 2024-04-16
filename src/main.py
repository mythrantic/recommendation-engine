from typing import Union, Optional
import debugpy
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI, Query, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
import httpx
import os
import pandas as pd
from r_engine.manga_data.embed_data_api import MangaVectorizer, MangaDatabase

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
async def recomend_manga(title: str = Query(..., example="Rebirth Of The Immortal Venerable"), size: Optional[int] = 18):
    manga_data = pd.read_csv('./files/mangas_embedd.csv')
    manga_data.drop_duplicates(subset=['title'], inplace=True)
    manga_data.fillna('', inplace=True)

    vectorizer = MangaVectorizer(manga_data)
    vectorized_mangas = vectorizer.vectorize_mangas(['title', 'description', 'authors', 'genres', 'rating', 'views', 'latestChapter', 'lastUpdated'])

    db_manager = MangaDatabase("./data/manga-db")
    table = db_manager.create_table("manga_set", data=vectorized_mangas.to_dict(orient='records'))

    query_vector = vectorized_mangas.loc[vectorized_mangas['title'] == title, 'vector'].iloc[0]
    result = db_manager.search("manga_set", query_vector, limit=size)
    print(result)

    return result


@app.get("/api/movies")
async def recomend_movie(title: str = Query(..., example="Rogue One: A Star Wars Story (2016)"), size: Optional[int] = 1):
    search_results = await recomend_movies(title=title, size=size)
    return search_results

Instrumentator().instrument(app).expose(app)