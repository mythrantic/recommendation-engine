from typing import Optional
import debugpy
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import pandas as pd
from .r_engine.manga_data.embed_data_api import MangaVectorizer, MangaDatabase
from .r_engine.movie_data.main import get_recommendations, data
import src.r_engine.movie_data.main
import lancedb
import numpy as np

file_dir = os.path.dirname(os.path.realpath(__file__))


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
    manga_data = pd.read_csv(file_dir + '/r_engine/manga_data/files/mangas_embedd.csv')
    manga_data.drop_duplicates(subset=['title'], inplace=True)
    manga_data.fillna('', inplace=True)

    vectorizer = MangaVectorizer(manga_data)
    vectorized_mangas = vectorizer.vectorize_mangas(
        ['title', 'description', 'authors', 'genres', 'rating', 'views', 'latestChapter', 'lastUpdated'])

    db_manager = MangaDatabase(file_dir + "/r_engine/manga_data/data/manga-db")
    table = db_manager.create_table(
        "manga_set", data=vectorized_mangas.to_dict(orient='records'))

    query_vector = vectorized_mangas.loc[vectorized_mangas['title']
                                         == title, 'vector'].iloc[0]
    result = db_manager.search("manga_set", query_vector, limit=size)
    print(result)

    return result


@app.get("/api/movies")
async def recomend_movie(title: str = Query(..., example="Rogue One: A Star Wars Story (2016)"), size: Optional[int] = 10):
    ratings = pd.read_csv('src/r_engine/movie_data/files/ratings.csv', header=None,
                          names=["user id", "movie id", "rating", "timestamp"])
    ratings = ratings.drop(columns=['timestamp'])
    ratings = ratings.drop(0)
    ratings["rating"] = ratings["rating"].values.astype(np.float32)
    ratings["user id"] = ratings["user id"].values.astype(np.int32)
    ratings["movie id"] = ratings["movie id"].values.astype(np.int32)

    reviewmatrix = ratings.pivot(
        index="user id", columns="movie id", values="rating").fillna(0)

    # SVD
    matrix = reviewmatrix.values
    u, s, vh = np.linalg.svd(matrix, full_matrices=False)

    vectors = np.rot90(np.fliplr(vh))
    print(vectors.shape)

    # Metadata
    movies = pd.read_csv('src/r_engine/movie_data/files/movies.csv', header=0,
                         names=["movie id", "title", "genres"])
    movies = movies[movies['movie id'].isin(reviewmatrix.columns)]

    for i in range(len(movies)):
        data.append({"id": movies.iloc[i]["movie id"], "title": movies.iloc[i]
                    ['title'], "vector": vectors[i], "genre": movies.iloc[i]['genres']})
    print(pd.DataFrame(data))

    # Connect to LanceDB

    db = lancedb.connect("src/r_engine/movie_data/data/test-db")
    try:
        src.r_engine.movie_data.main.table = db.create_table("movie_set", data=data)
    except:
        src.r_engine.movie_data.main.table = db.open_table("movie_set")

    results = get_recommendations(title, size)
    
    return results

Instrumentator().instrument(app).expose(app)
