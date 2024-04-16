import lancedb
import os
import numpy as np
import pandas as pd

global data
data = []
global table
table = None


# Find the directory in which the current script resides:
file_dir = os.path.dirname(os.path.realpath(__file__))


def get_recommendations(title, limit=5):
    pd_data = pd.DataFrame(data)
    # Table Search
    result = table.search(
        pd_data[pd_data['title'] == title]["vector"].values[0]).limit(limit).to_pandas()

    # Get IMDB links
    links = pd.read_csv(file_dir + '/files/links.csv', header=0,
                        names=["movie id", "imdb id", "tmdb id"], converters={'imdb id': str})

    ret = result['title'].values.tolist()
    # Loop to add links
    for i in range(len(ret)):
        link = links[links['movie id'] ==
                     result['id'].values[i]]["imdb id"].values[0]
        link = "https://www.imdb.com/title/tt" + link
        ret[i] = [ret[i], link]
    return ret


if __name__ == "__main__":

    # Load and prepare data
    ratings = pd.read_csv(file_dir + '/files/ratings.csv', header=None,
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
    movies = pd.read_csv(file_dir + '/files/movies.csv', header=0,
                         names=["movie id", "title", "genres"])
    movies = movies[movies['movie id'].isin(reviewmatrix.columns)]

    data = []
    for i in range(len(movies)):
        data.append({"id": movies.iloc[i]["movie id"], "title": movies.iloc[i]
                    ['title'], "vector": vectors[i], "genre": movies.iloc[i]['genres']})
    print(pd.DataFrame(data))

    # Connect to LanceDB

    db = lancedb.connect(file_dir + "/data/test-db")
    try:
        table = db.create_table("movie_set", data=data)
    except:
        table = db.open_table("movie_set")

    print(get_recommendations("Moana (2016)"))
    print(get_recommendations("Rogue One: A Star Wars Story (2016)"))
