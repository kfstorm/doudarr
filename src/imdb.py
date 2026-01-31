import asyncio
import logging
import os
import random
import re
import httpx
from .utils import get_response, new_http_client
from diskcache import Cache
from .config import app_config
from abc import ABC, abstractmethod
from typing import Any, Dict


class ImdbApi(ABC):
    def __init__(self):
        self.cache = Cache(os.path.join(app_config.cache_base_dir, "imdb"))

    def __exit__(self, exc_type, exc_value, traceback):
        self.cache.close()

    def get_cache(self) -> Cache:
        return self.cache

    @abstractmethod
    async def fetch_imdb_id(self, douban_id: str, douban_item: Any) -> str:
        pass

    async def get_imdb_id(self, douban_id: str, douban_item: Any) -> str:
        imdb_id = self.cache.get(douban_id, default="not_cached")
        if imdb_id != "not_cached":
            return imdb_id
        imdb_id = await self.fetch_imdb_id(douban_id, douban_item)
        if not imdb_id:
            expire = app_config.imdb_cache_ttl_id_not_found_seconds
        else:
            expire = None
        self.cache.set(douban_id, imdb_id, expire=expire)
        return imdb_id


class DoubanHtmlImdbApi(ImdbApi):
    def __init__(self):
        super().__init__()
        self.client = new_http_client()
        self.imdb_id_pattern = re.compile(r"IMDb:.*?(\btt\d+\b)")

    def _get_http_client_args(self) -> Dict[str, Any]:
        return {}

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
        super().__exit__(exc_type, exc_value, traceback)

    async def fetch_imdb_id(self, douban_id: str, douban_item: Any) -> str:
        title = douban_item["title"]

        await asyncio.sleep(
            random.uniform(0.0, app_config.imdb_request_delay_max_seconds)
        )

        logging.info(f"Fetching IMDb ID for {title} (douban ID: {douban_id})...")
        response = await get_response(
            self.client, f"https://movie.douban.com/subject/{douban_id}/"
        )
        match = self.imdb_id_pattern.search(response.text)
        if not match:
            logging.warning(f"IMDb ID not found for {title} (douban ID: {douban_id}).")
            return None
        imdb_id = match.group(1)
        logging.info(f"IMDb ID for {title} (douban ID: {douban_id}) is {imdb_id}.")

        return imdb_id


class DoubanIDatabaseImdbApi(ImdbApi):
    def __init__(self):
        super().__init__()
        self.client = new_http_client()
        self.client.base_url = app_config.douban_idatabase_url
        self.client.timeout = httpx.Timeout(app_config.douban_idatabase_timeout_seconds)
        if app_config.douban_idatabase_api_key:
            self.client.headers["X-API-Key"] = app_config.douban_idatabase_api_key

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
        super().__exit__(exc_type, exc_value, traceback)

    async def fetch_imdb_id(self, douban_id: str, douban_item: Any) -> str:
        title = douban_item["title"]

        logging.info(
            f"Fetching IMDb ID from douban-idatabase for {title} "
            + f"(douban ID: {douban_id})..."
        )

        try:
            response = await get_response(
                self.client, f"/api/item?douban_id={douban_id}"
            )
            items = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logging.warning(
                    f"Item not found in douban-idatabase for {title} "
                    + f"(douban ID: {douban_id})."
                )
                return None
            raise

        if not items or len(items) == 0:
            logging.warning(
                f"Empty response from douban-idatabase for {title} "
                + f"(douban ID: {douban_id})."
            )
            return None

        item = items[0]
        imdb_id = item.get("imdb_id")

        if not imdb_id:
            logging.warning(
                f"IMDb ID not available in douban-idatabase for {title} "
                + f"(douban ID: {douban_id})."
            )
            return None

        logging.info(
            f"IMDb ID for {title} (douban ID: {douban_id}) is {imdb_id} "
            + "(from douban-idatabase)."
        )
        return imdb_id


def get_imdb_api() -> ImdbApi:
    if app_config.douban_idatabase_url:
        return DoubanIDatabaseImdbApi()
    else:
        return DoubanHtmlImdbApi()
