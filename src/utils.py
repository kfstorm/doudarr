from typing import Any, AsyncIterator
from urllib.parse import urlparse
import httpx
import logging
from .config import app_config
from .throttler import throttler


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


def _get_extra_http_client_args():
    args = {}
    if app_config.proxy_address:
        args = {
            **args,
            "proxies": {
                "http://": app_config.proxy_address,
                "https://": app_config.proxy_address,
            },
        }
    if app_config.cookie_douban_com_dbcl2:
        cookies = httpx.Cookies()
        cookies.set("dbcl2", app_config.cookie_douban_com_dbcl2, domain=".douban.com")
        args = {
            **args,
            "cookies": cookies,
        }
    return args


def new_http_client() -> httpx.AsyncClient:
    client = httpx.AsyncClient(
        timeout=60,
        event_hooks=throttler.get_event_hooks(),
        **_get_extra_http_client_args(),
    )
    client.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        + " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.3"
    )
    return client


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
