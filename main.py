import logging
import traceback
from fastapi import FastAPI
import fastapi

from collection import CollectionApi
from imdb import DoubanHtmlImdbApi


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = FastAPI()
collection_api = CollectionApi()
imdb_api = DoubanHtmlImdbApi()


@app.exception_handler(500)
async def internal_exception_handler(request: fastapi.Request, exc: Exception):
    content = "".join(traceback.format_exception(exc))
    return fastapi.responses.PlainTextResponse(status_code=500, content=content)


@app.get("/collection/{collection_id}")
async def collection(collection_id: str):
    items = await collection_api.get_collection_items(collection_id)
    items = [await convert_item(item) for item in items]
    return items


async def convert_item(item):
    imdb_id = await imdb_api.get_imdb_id(item)
    return {
        "douban_id": item["id"],
        "title": item["title"],
        "imdb_id": imdb_id,
    }
