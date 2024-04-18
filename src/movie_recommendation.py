import pandas as pd
import numpy as np
import lancedb
from fastapi import Query
from r_engine.movie_data.main import get_recommendations, data
import os 

file_dir = os.path.dirname(os.path.realpath(__file__))


def recommend_movie(title: str = Query(..., example="Rogue One: A Star Wars Story (2016)"), size: int = 10):
    ratings = pd.read_csv(file_dir + '/r_engine/movie_data/files/ratings.csv', header=None,
                          names=["user id", "movie id", "rating", "timestamp"])
    ratings = ratings.drop(columns=['timestamp'])
    ratings = ratings.drop(0)
    ratings["rating"] = ratings["rating"].values.astype(np.float32)
    ratings["user id"] = ratings["user id"].values.astype(np.int32)
    ratings["movie id"] = ratings["movie id"].values.astype(np.int32)

    reviewmatrix = ratings.pivot(
        index="user id", columns="movie id", values="rating").fillna(0)

    matrix = reviewmatrix.values
    u, s, vh = np.linalg.svd(matrix, full_matrices=False)

    vectors = np.rot90(np.fliplr(vh))

    movies = pd.read_csv(file_dir + '/r_engine/movie_data/files/movies.csv', header=0,
                         names=["movie id", "title", "genres"])
    movies = movies[movies['movie id'].isin(reviewmatrix.columns)]

    for i in range(len(movies)):
        data.append({"id": movies.iloc[i]["movie id"], "title": movies.iloc[i]
                    ['title'], "vector": vectors[i], "genre": movies.iloc[i]['genres']})

    db = lancedb.connect(file_dir + "/r_engine/movie_data/data/test-db")
    try:
        table = db.create_table("movie_set", data=data)
    except:
        pass  # If the table already exists, we'll just skip creating it

    # Check if table was created successfully
    if table:
        results = get_recommendations(title, size)
        return results
    else:
        return {"error": "Failed to create database table"}


recommend_movie("Rogue One: A Star Wars Story (2016)", 10)
