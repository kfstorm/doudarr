import asyncio
import logging
import os
import random
import re
import httpx
from utils import get_http_client_args, get_response
from diskcache import Cache
from config import ImdbApiType, app_config
from abc import ABC, abstractmethod
from typing import Any


class ImdbApi(ABC):
    def __init__(self):
        self.cache = Cache(os.path.join(app_config.cache_base_dir, "imdb"))

    def __exit__(self, exc_type, exc_value, traceback):
        self.cache.close()

    @abstractmethod
    async def fetch_imdb_id(self, douban_item: Any):
        pass

    async def get_imdb_id(self, douban_item: Any):
        douban_id = douban_item["id"]
        imdb_id = self.cache.get(douban_id, default="not_cached")
        if imdb_id != "not_cached":
            return imdb_id
        imdb_id = await self.fetch_imdb_id(douban_item)
        if not imdb_id:
            expire = app_config.imdb_cache_ttl_id_not_found
        else:
            expire = None
        self.cache.set(douban_id, imdb_id, expire=expire)
        return imdb_id


class DoubanHtmlImdbApi(ImdbApi):
    def __init__(self):
        super().__init__()
        self.client = httpx.AsyncClient(**get_http_client_args())
        del self.client.headers["user-agent"]
        self.imdb_id_pattern = re.compile(r"IMDb:.*?(\btt\d+\b)")

    def _get_http_client_args(self):
        return {}

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
        super().__exit__(exc_type, exc_value, traceback)

    async def fetch_imdb_id(self, douban_item: Any):
        title = douban_item["title"]
        douban_id = douban_item["id"]

        await asyncio.sleep(random.uniform(0.0, app_config.imdb_request_delay_max))

        logging.info(f"Fetching IMDb ID for {title} (douban ID: {douban_id})...")
        response = await get_response(
            self.client, f"https://movie.douban.com/subject/{douban_id}/"
        )
        match = self.imdb_id_pattern.search(response.text)
        if not match:
            logging.warn(f"IMDb ID not found for {title} (douban ID: {douban_id}).")
            return None
        imdb_id = match.group(1)
        logging.info(f"IMDb ID for {title} (douban ID: {douban_id}) is {imdb_id}.")

        return imdb_id


def get_imdb_api() -> ImdbApi:
    logging.info(f"Using IMDb API type: {app_config.imdb_api_type}")
    if app_config.imdb_api_type == ImdbApiType.DOUBAN_HTML:
        return DoubanHtmlImdbApi()
    else:
        raise ValueError(f"Unsupported IMDb API type: {app_config.imdb_api_type}")
