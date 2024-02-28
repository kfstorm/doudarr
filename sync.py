import asyncio
import logging

from config import app_config
from imdb import ImdbApi
from utils import new_http_client


async def sync(imdb_api: ImdbApi):
    to_urls = app_config.sync_imdb_cache_to
    if to_urls:
        while True:
            logging.info("Syncing IMDb cache...")
            async with new_http_client() as client:
                try:
                    items = []
                    cache = imdb_api.get_cache()
                    for key in cache:
                        value, expire_time = cache.get(key, expire_time=True)
                        if value:
                            items.append(
                                {"key": key, "value": value, "expire_time": expire_time}
                            )
                    for url in to_urls:
                        try:
                            logging.info(f"Syncing {len(items)} IMDb items to {url}...")
                            response = await client.post(url, json=items)
                            response.raise_for_status()
                        except Exception:
                            logging.exception(f"Failed to sync IMDb cache to {url}.")
                    logging.info("Synced IMDb cache.")
                except Exception:
                    logging.exception("Failed to sync IMDb cache.")
            await asyncio.sleep(app_config.sync_imdb_cache_interval_seconds)
    else:
        logging.info(
            "Syncing IMDb cache is disabled because remote URLs are not configured."
        )
