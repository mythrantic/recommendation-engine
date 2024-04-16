import pandas as pd
from embed_data_api import MangaVectorizer, MangaDatabase

manga_data = pd.read_csv('./files/mangas_embedd.csv')
manga_data.drop_duplicates(subset=['title'], inplace=True)
manga_data.fillna('', inplace=True)

vectorizer = MangaVectorizer(manga_data)
vectorized_mangas = vectorizer.vectorize_mangas(['title', 'description', 'authors', 'genres', 'rating', 'views', 'latestChapter', 'lastUpdated'])

db_manager = MangaDatabase("./data/manga-db")
table = db_manager.create_table("manga_set", data=vectorized_mangas.to_dict(orient='records'))

query_vector = vectorized_mangas.loc[vectorized_mangas['title'] == "Rebirth Of The Immortal Venerable", 'vector'].iloc[0]
result = db_manager.search("manga_set", query_vector, limit=20)
print(result)
