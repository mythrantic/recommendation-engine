import httpx
import asyncio
import pandas as pd
import json
import os
import logging
from colorama import init, Fore
from httpx import Timeout
from tqdm.asyncio import tqdm
import tenacity

init(autoreset=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

BASE_URL = 'https://svelte-manga-api.valiantlynx.com'
timeout = Timeout(10.0, connect=60.0)

GENRES = ['Action', 'Adventure', 'Comedy', 'Cooking', 'Doujinshi', 'Drama', 'Erotica', 'Fantasy',
          'Gender bender', 'Harem', 'Historical', 'Horror', 'Isekai', 'Josei', 'Manhua', 'Manhwa',
          'Martial arts', 'Mature', 'Mecha', 'Medical', 'Mystery', 'One shot', 'Pornographic',
          'Psychological', 'Romance', 'School life', 'Sci fi', 'Seinen', 'Shoujo', 'Shoujo ai',
          'Shounen', 'Shounen ai', 'Slice of life', 'Smut', 'Sports', 'Supernatural', 'Tragedy',
          'Webtoons', 'Yaoi', 'Yuri']

# Define a retry decorator
retry_decorator = tenacity.retry(
    stop=tenacity.stop_after_attempt(3),  # Retry for a maximum of 3 attempts
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),  # Exponential backoff with jitter
    retry=tenacity.retry_if_exception_type(Exception)  # Retry on any exception
)

async def fetch_manga(server='MANGANELO', genre="", page=1):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(f'{BASE_URL}/api/manga', params={'server': server, 'genre': genre, 'page': page})
            if response.status_code == 200:
                return response.json().get('mangas', [])
            else:
                logger.error(f"{Fore.RED}Failed to fetch manga list for genre '{genre}' at page {page}")
                return []
        except Exception as e:
            logger.error(f"{Fore.RED}Exception occurred while fetching manga list: {e}")
            return []

# Apply retry decorator to fetch_manga_details function as well
@retry_decorator
async def fetch_manga_details(manga_id, server='MANGANELO'):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(f'{BASE_URL}/api/manga/{manga_id}', params={'server': server})
            if response.status_code == 200:
                manga_details = response.json()
                # Clean the description to remove newline characters
                manga_details['description'] = manga_details['description'].replace('\n', ' ')
                return manga_details
            else:
                logger.error(f"{Fore.RED}Failed to fetch details for manga ID {manga_id}")
                return {}
        except Exception as e:
            logger.error(f"{Fore.RED}Exception occurred while fetching manga details: {e}")
            return {}

# Apply retry decorator to append_to_csv function as well
@retry_decorator
async def append_to_csv(df, filename='./files/mangas_embedd.csv'):
    file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0
    # Clean the description column
    df['description'] = df['description'].str.replace('\n', ' ')
    df.to_csv(filename, mode='a', header=not file_exists, index=False)

async def fetch_details_for_mangas(manga_list):
    return await asyncio.gather(*(fetch_manga_details(manga['id']) for manga in manga_list))

async def main():
    checkpoint_file = './files/manga_checkpoint.json'
    processed_manga_ids, checkpoint = set(), {'genre_index': 0, 'page': 1, 'processed_manga_ids': []}
    try:
        with open(checkpoint_file) as file:
            checkpoint = json.load(file)
            processed_manga_ids.update(checkpoint.get('processed_manga_ids', []))
    except FileNotFoundError:
        logger.info(f"{Fore.YELLOW}Checkpoint file not found, starting from scratch.")

    for genre_index, genre in enumerate(GENRES[checkpoint['genre_index']:], start=checkpoint['genre_index']):
        page = checkpoint['page']
        logger.info(f"{Fore.CYAN}Processing genre: {genre}")

        tasks = []
        async for page in tqdm(range(checkpoint['page'], 51), desc=f"{genre}", leave=True):
            current_mangas = await fetch_manga(genre=genre, page=page)
            if not current_mangas:
                break

            try:
                manga_details_list = await fetch_details_for_mangas(current_mangas)
            except Exception as e:
                logger.error(f"Exception occurred while fetching manga details: {e}")
                continue

            for manga, details in zip(current_mangas, manga_details_list):
                if manga['id'] not in processed_manga_ids and details:
                    manga.update({
                        'authors': '|'.join(str(x) for x in details.get('authors', [])),
                        'genres': '|'.join(str(x) for x in details.get('genres', [])),
                        'lastUpdated': details['lastUpdated'],
                        'views': details['views']
                    })
                    processed_manga_ids.add(manga['id'])

            new_data_df = pd.DataFrame(current_mangas).drop_duplicates(subset=['id'])
            tasks.append(append_to_csv(new_data_df))  # Append the coroutine to the task list
            checkpoint.update({'genre_index': genre_index, 'page': page + 1, 'processed_manga_ids': list(processed_manga_ids)})
            with open(checkpoint_file, 'w') as file:
                json.dump(checkpoint, file)


        checkpoint['page'] = 1

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
