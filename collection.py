import asyncio
import logging
import os
import random
from typing import Any, List
import httpx
from utils import get_http_client_args, get_json
from diskcache import Cache
from config import app_config


class BaseApi:
    def __init__(self, sub_path: str, cache_name: str, items_key: str):
        self.client = httpx.AsyncClient(
            **get_http_client_args(),
            base_url=f"https://m.douban.com/rexxar/api/v2/{sub_path}",
        )
        del self.client.headers["user-agent"]
        self.client.headers["Referer"] = f"https://m.douban.com/{sub_path}"
        self.cache = Cache(os.path.join(app_config.cache_base_dir, cache_name))
        self.items_key = items_key

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
        self.cache.close()

    def get_cache(self) -> Cache:
        return self.cache

    async def get_info(self, id: str) -> Any:
        return await get_json(self.client, f"/{id}")

    async def get_items(self, id: str) -> List[Any]:
        items = self.cache.get(id)
        if items is not None:
            return items

        logging.info(f"Fetching items for {id} ...")
        total = None
        items = []
        start = 0
        count = 50
        while total is None or start < total:
            response = await get_json(
                self.client,
                f"/{id}/items?start={start}&count={count}",
            )
            if total is None:
                total = response["total"]
            items.extend(response[self.items_key])
            start += count
            await asyncio.sleep(
                random.uniform(0, app_config.douban_api_request_delay_max)
            )
        logging.info(f"Fetched {len(items)} items for {id}.")

        self.cache.set(id, items, expire=app_config.collection_cache_ttl)
        return items


class CollectionApi(BaseApi):
    def __init__(self):
        super().__init__("subject_collection", "collection", "subject_collection_items")


class DoulistApi(BaseApi):
    def __init__(self):
        super().__init__("doulist", "doulist", "items")
