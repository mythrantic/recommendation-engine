import pandas as pd
from .embed_data_api import MangaVectorizer, MangaDatabase
import os

def manga_recommendations(title, size):
    file_dir = os.path.dirname(os.path.realpath(__file__))
    manga_data = pd.read_csv(file_dir + '/files/mangas_embedd.csv')
    manga_data.drop_duplicates(subset=['title'], inplace=True)
    manga_data.fillna('', inplace=True)

    vectorizer = MangaVectorizer(manga_data)
    vectorized_mangas = vectorizer.vectorize_mangas(['title', 'description', 'authors', 'genres', 'rating', 'views', 'latestChapter', 'lastUpdated'])

    db_manager = MangaDatabase(file_dir + "/data/manga-db")
    table = db_manager.create_table("manga_set", data=vectorized_mangas.to_dict(orient='records'))

    query_vector = vectorized_mangas.loc[vectorized_mangas['title'] == title, 'vector'].iloc[0]
    result = db_manager.search("manga_set", query_vector, limit=size)
    
    # Construct return with title and manga ID sorted by distance
    sorted_results = result.sort_values(by='_distance')  # Sort by distance
    return_list = [{'title': row['title'], 'manga_id': row['id']} for _, row in sorted_results.iterrows()]

    return return_list
    
manga_recommendations(title="Rebirth Of The Immortal Venerable", size=10)

