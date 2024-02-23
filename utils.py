from urllib.parse import urlparse
import httpx
import logging
from config import app_config


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
    if app_config.proxy_address:
        return {
            "proxies": {
                "http://": app_config.proxy_address,
                "https://": app_config.proxy_address,
            },
        }
    else:
        return {}


def get_douban_id(item):
    parsed_url = urlparse(item["url"])
    douban_id = [_ for _ in parsed_url.path.split("/") if _][-1]
    return douban_id
