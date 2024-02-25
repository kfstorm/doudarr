from typing import Any, AsyncIterator
from urllib.parse import urlparse
import httpx
import logging
from config import app_config
from throttler import throttler


async def get_response(client: httpx.AsyncClient, url: str):
    response = await client.get(url)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logging.error(f"Failed to fetch {url}: {e}")
        raise e
    return response


async def get_json(client: httpx.AsyncClient, url: str):
    response = await get_response(client, url)
    return response.json()


def get_http_client_args():
    args = {
        **throttler.get_client_args(),
    }
    if app_config.proxy_address:
        args = {
            **args,
            "proxies": {
                "http://": app_config.proxy_address,
                "https://": app_config.proxy_address,
            },
        }
    return args


def get_douban_id(item):
    parsed_url = urlparse(item["url"])
    douban_id = [_ for _ in parsed_url.path.split("/") if _][-1]
    return douban_id


async def read_pages(
    read_one_page, get_total, get_items, items_per_page
) -> AsyncIterator[Any]:
    total = None
    start = 0
    count = items_per_page
    while total is None or start < total:
        page_data = await read_one_page(start, count)
        if total is None:
            total = get_total(page_data)
        new_items = get_items(page_data)
        for item in new_items:
            yield item
        start += len(new_items)
        if not new_items:
            break
