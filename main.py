import asyncio
import logging
import traceback
from typing import Any, List
from fastapi import FastAPI
import fastapi
from bootstrap import bootstrap

from lists import CollectionApi, DoulistApi
from imdb import get_imdb_api
from utils import get_douban_id


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = FastAPI()
collection_api = CollectionApi()
doulist_api = DoulistApi()
imdb_api = get_imdb_api()

asyncio.create_task(bootstrap(collection_api, doulist_api, imdb_api))


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
        }
    }


@app.get("/collection/{id}")
async def collection(id: str) -> List[Any]:
    items = await collection_api.get_items(id)
    # Keep only movies
    items = [item for item in items if item["type"] == "movie"]
    items = [await convert_item(item) for item in items]
    # Keep only items with IMDb ID
    items = [item for item in items if item["imdb_id"]]
    return items


@app.get("/doulist/{id}")
async def doulist(id: str) -> List[Any]:
    items = await doulist_api.get_items(id)
    # Keep only movies
    items = [item for item in items if item["type"] == "movie"]
    items = [await convert_item(item) for item in items]
    # Keep only items with IMDb ID
    items = [item for item in items if item["imdb_id"]]
    return items


async def convert_item(item: Any) -> Any:
    douban_id = get_douban_id(item)
    imdb_id = await imdb_api.get_imdb_id(douban_id, item)
    return {
        "douban_id": douban_id,
        "title": item["title"],
        "imdb_id": imdb_id,
    }
