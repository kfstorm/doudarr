import asyncio
import logging
import os
import random
import httpx
from utils import get_json
from diskcache import Cache
from config import app_config


class CollectionApi:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url="https://m.douban.com/rexxar/api/v2/subject_collection"
        )
        del self.client.headers["user-agent"]
        self.client.headers["Referer"] = "https://m.douban.com/subject_collection"
        self.cache = Cache(os.path.join(app_config.cache_base_dir, "collection"))

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
        self.cache.close()

    async def get_collection_items(self, collection_id: str):
        items = self.cache.get(collection_id)
        if items is not None:
            return items

        logging.info(f"Fetching collection items for {collection_id} ...")
        collection_info = await get_json(self.client, f"/{collection_id}")
        total = collection_info["total"]
        items = []
        start = 0
        count = 50
        while start < total:
            response = await get_json(
                self.client,
                f"/{collection_id}/items?start={start}&count={count}",
            )
            items.extend(response["subject_collection_items"])
            start += count
            await asyncio.sleep(
                random.uniform(0, app_config.collection_request_delay_max)
            )
        logging.info(f"Fetched {len(items)} items for {collection_id}.")

        self.cache.set(collection_id, items, expire=app_config.collection_cache_ttl)
        return items