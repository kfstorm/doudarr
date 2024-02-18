import asyncio
import logging
import random
import re
import traceback
from fastapi import FastAPI
import fastapi
import httpx
from diskcache import Cache


COLLECTION_CACHE = Cache("cache/collection")
IMDB_CACHE = Cache("cache/imdb")

DOUBAN_COLLECTION_API_PREFIX = "https://m.douban.com/rexxar/api/v2/subject_collection"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)


def get_http_client():
    client = httpx.AsyncClient()
    del client.headers["user-agent"]
    client.headers["Referer"] = "https://m.douban.com/subject_collection"
    return client


async def get_response(client: httpx.AsyncClient, url: str):
    response = await client.get(url)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logging.error(
            f"Response headers: {response.headers}. Response body: {response.content}"
        )
        raise e
    return response


async def get_json(client: httpx.AsyncClient, url: str):
    response = await get_response(client, url)
    return response.json()


async def get_collection_items(client: httpx.AsyncClient, collection_id: str):
    cache = COLLECTION_CACHE
    items = cache.get(collection_id)
    if items is not None:
        return items

    logging.info(f"Fetching collection items for {collection_id}...")
    collection_info = await get_json(
        client, f"{DOUBAN_COLLECTION_API_PREFIX}/{collection_id}"
    )
    total = collection_info["total"]
    items = []
    start = 0
    count = 50
    while start < total:
        response = await get_json(
            client,
            f"{DOUBAN_COLLECTION_API_PREFIX}/{collection_id}/items?start={start}&count={count}",
        )
        items.extend(response["subject_collection_items"])
        start += count
        await asyncio.sleep(random.uniform(0.0, 0.1))
    logging.info(f"Fetched {len(items)} items for {collection_id}.")

    cache.set(collection_id, items, expire=3600)
    return items


app = FastAPI()


@app.exception_handler(500)
async def internal_exception_handler(request: fastapi.Request, exc: Exception):
    content = "".join(traceback.format_exception(exc))
    return fastapi.responses.PlainTextResponse(status_code=500, content=content)


@app.get("/collection/{collection_id}")
async def collection(collection_id: str):
    async with get_http_client() as client:
        items = await get_collection_items(client, collection_id)
        items = [await convert_item(client, item) for item in items]
        return items


async def convert_item(client: httpx.AsyncClient, item):
    imdb_id = await get_imdb_id_from_douban_id(client, item["title"], item["id"])
    return {
        "douban_id": item["id"],
        "douban_url": item["url"],
        "douban_rating": item["rating"],
        "title": item["title"],
        "poster_url": item["cover_url"],
        "imdb_id": imdb_id,
    }


IMDB_ID_PATTERN = re.compile(r"IMDb:.*?(\btt\d+\b)")


async def get_imdb_id_from_douban_id(
    client: httpx.AsyncClient, title: str, douban_id: str
):
    cache = IMDB_CACHE
    imdb_id = cache.get(douban_id)
    if imdb_id is not None:
        return imdb_id

    await asyncio.sleep(random.uniform(0.0, 1.0))

    logging.info(f"Fetching IMDb ID for {title} (douban ID: {douban_id})...")
    response = await get_response(
        client, f"https://movie.douban.com/subject/{douban_id}/"
    )
    match = IMDB_ID_PATTERN.search(response.text)
    if not match:
        raise ValueError(f"IMDb ID not found for douban ID: {douban_id}")
    imdb_id = match.group(1)
    logging.info(f"IMDb ID for {title} (douban ID: {douban_id}) is {imdb_id}.")

    cache.set(douban_id, imdb_id)
    return imdb_id
