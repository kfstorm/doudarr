import asyncio
import logging
import time
import traceback
from typing import Any, List
from fastapi import FastAPI, HTTPException
import fastapi
from .bootstrap import bootstrap
from .sync import sync

from .lists import BaseApi, CollectionApi, DoulistApi
from .imdb import get_imdb_api
from .throttler import throttler
from .utils import get_douban_id
from .config import app_config


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = FastAPI()
collection_api = CollectionApi()
doulist_api = DoulistApi()
imdb_api = get_imdb_api()

asyncio.create_task(bootstrap(collection_api, doulist_api, imdb_api))
asyncio.create_task(sync(imdb_api))


@app.exception_handler(500)
async def internal_exception_handler(request: fastapi.Request, exc: Exception):
    content = "".join(traceback.format_exception(exc))
    return fastapi.responses.PlainTextResponse(status_code=500, content=content)


@app.get("/")
@app.get("/stats")
async def stats() -> Any:
    return {
        "cache_size": {
            "collection": len(collection_api.get_cache()),
            "doulist": len(doulist_api.get_cache()),
            "imdb": len(imdb_api.get_cache()),
        },
        "throttler_info": throttler.get_info(),
    }


@app.post("/sync")
async def sync(apikey: str, items: List[Any]) -> Any:
    if not apikey or not app_config.apikey or apikey != app_config.apikey:
        raise HTTPException(status_code=403, detail="Invalid API key.")
    cache = imdb_api.get_cache()
    now = time.time()
    count = 0
    new_count = 0
    for item in items:
        key = item["key"]
        value = item["value"]
        expire_time = item["expire_time"]
        if expire_time and expire_time <= now:
            continue
        old_value, old_expire_time = cache.get(
            key, default="not_found", expire_time=True
        )
        if (
            old_value == "not_found"
            or not expire_time
            or (old_expire_time and expire_time > old_expire_time)
        ):
            expire = expire_time - now if expire_time else None
            cache.set(key, value, expire=expire)
            count += 1
            if old_value == "not_found":
                new_count += 1
    logging.info(f"Synced {count} IMDb items from remote. New items: {new_count}.")


async def list(list_api: BaseApi, id: str, min_rating: float) -> List[Any]:
    items = await list_api.get_items(id)
    # Keep only movies
    items = [item for item in items if item["type"] == "movie"]
    # Keep only items with a minimum score
    if min_rating:
        items = [
            item
            for item in items
            if "rating" in item
            and "value" in item["rating"]
            and item["rating"]["value"] >= min_rating
        ]
    items = [await convert_item(item) for item in items]
    # Keep only items with IMDb ID
    items = [item for item in items if item["imdb_id"]]
    return items


@app.get("/collection/{id}")
async def collection(id: str, min_rating: float = None) -> List[Any]:
    return await list(collection_api, id, min_rating)


@app.get("/doulist/{id}")
async def doulist(id: str, min_rating: float = None) -> List[Any]:
    return await list(doulist_api, id, min_rating)


async def convert_item(item: Any) -> Any:
    douban_id = get_douban_id(item)
    imdb_id = await imdb_api.get_imdb_id(douban_id, item)
    return {
        "douban_id": douban_id,
        "title": item["title"],
        "imdb_id": imdb_id,
    }
