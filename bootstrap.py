import asyncio
import logging
from collections import deque
from collection import CollectionApi
from imdb import ImdbApi
from config import app_config
from utils import get_douban_id


COMMON_COLLECTIONS = [
    "movie_top250",  # 豆瓣电影 Top250
    "movie_weekly_best",  # 一周口碑电影榜
    "movie_real_time_hotest",  # 实时热门电影
    "subject_real_time_hotest",  # 实时热门书影音
]


async def bootstrap(collection_api: CollectionApi, imdb_api: ImdbApi):
    """
    This function is called at the start of the application to regularly send
    HTTP requests and cache the results.

    This can help saving time on incoming requests.
    """
    while True:
        logging.info("Bootstrapping...")
        all_collections = deque(COMMON_COLLECTIONS)
        visited_collections = set()
        while (
            all_collections
            and len(visited_collections) < app_config.bootstrap_collections_max
        ):
            collection_id = all_collections.popleft()
            visited_collections.add(collection_id)

            try:
                info = await collection_api.get_info(collection_id)
                for related_collection in info["related_charts"]["items"]:
                    related_collection_id = related_collection["id"]
                    if related_collection_id not in visited_collections:
                        all_collections.append(related_collection_id)

                items = await collection_api.get_items(collection_id)
                # Keep only movies
                items = [item for item in items if item["type"] == "movie"]
                for item in items:
                    douban_id = get_douban_id(item)
                    await imdb_api.get_imdb_id(douban_id, item)
            except Exception as e:
                logging.error(f"Failed to fetch collection {collection_id}: {e}")

            await asyncio.sleep(app_config.bootstrap_collection_interval)
        logging.info("Bootstrapping done.")
        await asyncio.sleep(app_config.bootstrap_interval)
