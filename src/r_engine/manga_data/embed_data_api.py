import lancedb
import numpy as np
import pandas as pd
from hashlib import md5

class MangaVectorizer:
    def __init__(self, manga_data):
        self.manga_data = manga_data
        
    def encode_text(self, text):
        """Simplified encoding for text attributes to a fixed-size vector."""
        hash_digest = md5(text.encode('utf-8')).hexdigest()
        return np.array([int(hash_digest[i:i+2], 16) for i in range(0, len(hash_digest), 2)])

    def encode_numeric(self, value, max_value):
        """Normalize numeric values."""
        return np.array([float(value) / max_value])

    def encode_date(self, date_str):
        """Convert dates into a timestamp."""
        try:
            return np.array([pd.to_datetime(date_str).timestamp()])
        except:
            return np.array([0.0])
    
    def generate_vector(self, manga, attributes):
        vector_parts = []
        if 'title' in attributes:
            vector_parts.append(self.encode_text(manga['title']))
        if 'description' in attributes:
            vector_parts.append(self.encode_text(manga['description']))
        if 'authors' in attributes:
            vector_parts.append(self.encode_text(manga['authors']))
        if 'genres' in attributes:
            vector_parts.append(self.encode_text(manga['genres']))
        if 'rating' in attributes:
            vector_parts.append(self.encode_numeric(manga['rating'], 5))  # Assuming rating is out of 5
        if 'views' in attributes:
            vector_parts.append(self.encode_numeric(manga['views'], 1e9))  # Assuming max views is 1 billion for normalization
        if 'latestChapter' in attributes:
            vector_parts.append(self.encode_text(manga['latestChapter']))
        if 'lastUpdated' in attributes:
            vector_parts.append(self.encode_date(manga['lastUpdated']))
        return np.concatenate(vector_parts)

    def vectorize_mangas(self, attributes):
        self.manga_data['vector'] = self.manga_data.apply(lambda row: self.generate_vector(row, attributes), axis=1)
        return self.manga_data[['id', 'title', 'vector']]

class MangaDatabase:
    def __init__(self, db_path):
        self.db = lancedb.connect(db_path)
        
    def create_table(self, table_name, data):
        try:
            self.db.drop_table(table_name)
        except Exception as e:
            print("Dropping table failed:", e)
        return self.db.create_table(table_name, data=data)

    def search(self, table_name, query_vector, limit=10):
        table = self.db.open_table(table_name)
        result = table.search(query_vector).limit(limit + 1).to_pandas()
        return result



# Example usage
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
