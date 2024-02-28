import asyncio
import logging
import os
import random
from typing import Any, AsyncIterator, List
from .utils import get_json, new_http_client, read_pages
from diskcache import Cache
from .config import app_config


class BaseApi:
    def __init__(self, sub_path: str, cache_name: str, items_key: str):
        self.client = new_http_client()
        self.client.base_url = f"https://m.douban.com/rexxar/api/v2/{sub_path}"
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

    async def _read_one_page(self, id: str, start: int, count: int) -> Any:
        await asyncio.sleep(
            random.uniform(0, app_config.douban_api_request_delay_max_seconds)
        )
        return await get_json(
            self.client,
            f"/{id}/items?start={start}&count={count}",
        )

    async def get_items(self, id: str) -> List[Any]:
        items = self.cache.get(id)
        if items is not None:
            return items

        logging.info(f"Fetching items for {id} ...")
        items = [
            _
            async for _ in read_pages(
                read_one_page=lambda start, count: self._read_one_page(
                    id, start, count
                ),
                get_total=lambda page_data: page_data["total"],
                get_items=lambda page_data: page_data[self.items_key],
                items_per_page=50,
            )
        ]
        logging.info(f"Fetched {len(items)} items for {id}.")

        self.cache.set(id, items, expire=app_config.list_cache_ttl_seconds)
        return items


class CollectionApi(BaseApi):
    def __init__(self):
        super().__init__("subject_collection", "collection", "subject_collection_items")


class DoulistApi(BaseApi):
    def __init__(self):
        super().__init__("doulist", "doulist", "items")


# Reference:
# https://github.com/DIYgod/RSSHub/blob/master/lib/v2/douban/other/recommended.js
class ListsApi:
    def __init__(self):
        self.client = new_http_client()
        self.client.base_url = "https://frodo.douban.com/api/v2"
        self.client.headers["User-Agent"] = "MicroMessenger/"
        self.client.headers[
            "Referer"
        ] = "https://servicewechat.com/wx2f9b06c1de1ccfca/91/page-frame.html"
        self.api_key = "0ac44ae016490db2204ce0a042db2916"

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()

    async def _read_one_page(self, start: int, count: int) -> Any:
        await asyncio.sleep(
            random.uniform(0, app_config.douban_api_request_delay_max_seconds)
        )
        return await get_json(
            self.client,
            f"/skynet/new_playlists?apikey={self.api_key}&subject_type=movie&start={start}&count={count}",
        )

    async def iter_lists(self) -> AsyncIterator[Any]:
        async for item in read_pages(
            read_one_page=lambda start, count: self._read_one_page(start, count),
            get_total=lambda page_data: page_data["total"],
            get_items=lambda page_data: page_data["data"][0]["items"],
            items_per_page=50,
        ):
            yield item
