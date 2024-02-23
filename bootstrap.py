import asyncio
import logging
import random
from typing import List, Tuple
from urllib.parse import urlparse
from lists import CollectionApi, DoulistApi, ListsApi
from imdb import ImdbApi
from config import app_config
from utils import get_douban_id


async def bootstrap(
    collection_api: CollectionApi, doulist_api: DoulistApi, imdb_api: ImdbApi
):
    """
    This function is called at the start of the application to regularly send
    HTTP requests and cache the results.

    This can help saving time on incoming requests.
    """

    list_apis = {
        "collection": collection_api,
        "doulist": doulist_api,
    }

    while True:
        logging.info("Bootstrapping...")
        lists = await get_lists_to_bootstrap()
        for type, id in lists:
            try:
                list_api = list_apis[type]
                items = await list_api.get_items(id)
                # Keep only movies
                items = [item for item in items if item["type"] == "movie"]
                for item in items:
                    douban_id = get_douban_id(item)
                    await imdb_api.get_imdb_id(douban_id, item)
            except Exception as e:
                logging.error(f"Failed to fetch {type} {id}: {e}")

            await asyncio.sleep(app_config.bootstrap_list_interval)
        logging.info("Bootstrapping done.")
        await asyncio.sleep(app_config.bootstrap_interval)


async def get_lists_to_bootstrap() -> List[Tuple[str, str]]:
    lists_api = ListsApi()
    lists = set()
    async for item in lists_api.iter_lists():
        parsed_url = urlparse(item["sharing_url"])
        url_parts = [_ for _ in parsed_url.path.split("/") if _][-2:]
        list_type = url_parts[0]
        list_id = url_parts[1]
        if list_type == "subject_collection":
            lists.add(("collection", list_id))
        elif list_type == "doulist":
            lists.add(("doulist", list_id))
        else:
            logging.warning(f"Unknown list type: {list_type}")
        if len(lists) >= app_config.bootstrap_lists_max * 10:
            break

    lists = random.sample(list(lists), app_config.bootstrap_lists_max)
    return lists
