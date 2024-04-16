import lancedb
import numpy as np
import pandas as pd
from hashlib import md5

# Load manga data
mangas = pd.read_csv('./files/mangas_embedd.csv')
mangas.drop_duplicates(subset=['title'], inplace=True)
mangas.fillna('', inplace=True)  # Handle missing values

# Encoding functions for different attributes
def encode_text(text):
    """Simplified encoding for text attributes to a fixed-size vector."""
    hash_digest = md5(text.encode('utf-8')).hexdigest()
    return np.array([int(hash_digest[i:i+2], 16) for i in range(0, len(hash_digest), 2)])

def encode_numeric(value, max_value):
    """Normalize numeric values."""
    return np.array([float(value) / max_value])

def encode_date(date_str):
    """Convert dates into a timestamp."""
    try:
        return np.array([pd.to_datetime(date_str).timestamp()])
    except:
        return np.array([0.0])
    
    
# Vector generation for each manga based on specified attributes
def generate_vector(manga, attributes):
    vector_parts = []
    if 'title' in attributes:
        vector_parts.append(encode_text(manga['title']))
    if 'description' in attributes:
        vector_parts.append(encode_text(manga['description']))
    if 'authors' in attributes:
        vector_parts.append(encode_text(manga['authors']))
    if 'genres' in attributes:
        vector_parts.append(encode_text(manga['genres']))
    if 'rating' in attributes:
        vector_parts.append(encode_numeric(manga['rating'], 5))  # Assuming rating is out of 5
    if 'views' in attributes:
        vector_parts.append(encode_numeric(manga['views'], 1e9))  # Assuming max views is 1 billion for normalization
    if 'latestChapter' in attributes:
        vector_parts.append(encode_text(manga['latestChapter']))
    if 'lastUpdated' in attributes:
        vector_parts.append(encode_date(manga['lastUpdated']))
    return np.concatenate(vector_parts)

# Prepare data for LanceDB with dynamic attribute selection
attributes = ['title', 'description', 'authors', 'genres', 'rating', 'views', 'latestChapter', 'lastUpdated']
mangas['vector'] = mangas.apply(lambda row: generate_vector(row, attributes), axis=1)

data = [{
    "id": row['id'],
    "title": row['title'],
    "vector": row['vector'].tolist(),
} for index, row in mangas.iterrows()]

# Connect to LanceDB
db = lancedb.connect("./data/manga-db")
try:
    db.drop_table("manga_set")
except Exception as e:
    print("Dropping table failed:", e)

table = db.create_table("manga_set", data=data)

def get_recommendations(query_title, limit=10):
    query_vector = next(row['vector'] for index, row in mangas.iterrows() if row["title"] == query_title)
    result = table.search(query_vector).limit(limit + 1).to_pandas()
    return result[result['title'] != query_title][['title']].head(limit)

# Example usage
print(get_recommendations("Rebirth Of The Immortal Venerable", limit=20))
