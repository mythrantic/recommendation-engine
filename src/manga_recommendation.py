import pandas as pd
from fastapi import Query
from .r_engine.manga_data.embed_data_api import MangaVectorizer, MangaDatabase
import os 

file_dir = os.path.dirname(os.path.realpath(__file__))


def recommend_manga(title: str = Query(..., example="Rebirth Of The Immortal Venerable"), size: int = 18):
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
    result_dict = result.to_dict(orient='records')
    
    return result_dict
