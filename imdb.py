import asyncio
import logging
import os
import random
import re
import httpx
from utils import get_response
from diskcache import Cache
from config import app_config
from abc import ABC, abstractmethod
from typing import Any


class ImdbApi(ABC):
    @abstractmethod
    async def get_imdb_id(self, douban_item: Any):
        pass


IMDB_ID_PATTERN = re.compile(r"IMDb:.*?(\btt\d+\b)")


class DoubanHtmlImdbApi(ImdbApi):
    def __init__(self):
        self.client = httpx.AsyncClient(base_url="https://movie.douban.com/subject")
        self.cache = Cache(os.path.join(app_config.cache_base_dir, "imdb"))

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
        self.cache.close()

    async def get_imdb_id(self, douban_item: Any):
        title = douban_item["title"]
        douban_id = douban_item["id"]
        imdb_id = self.cache.get(douban_id)
        if imdb_id is not None:
            return imdb_id

        await asyncio.sleep(random.uniform(0.0, app_config.imdb_request_delay_max))

        logging.info(f"Fetching IMDb ID for {title} (douban ID: {douban_id})...")
        response = await get_response(
            self.client, f"https://movie.douban.com/subject/{douban_id}/"
        )
        match = IMDB_ID_PATTERN.search(response.text)
        if not match:
            raise ValueError(f"IMDb ID not found for douban ID: {douban_id}")
        imdb_id = match.group(1)
        logging.info(f"IMDb ID for {title} (douban ID: {douban_id}) is {imdb_id}.")

        self.cache.set(douban_id, imdb_id)
        return imdb_id
