from enum import Enum
from typing import List
from pydantic_settings import BaseSettings


class ImdbApiType(str, Enum):
    DOUBAN_HTML = "DOUBAN_HTML"


class AppConfig(BaseSettings):
    cache_base_dir: str = "cache"
    douban_api_request_delay_max_seconds: float = 1
    list_cache_ttl_seconds: float = 3600 * 24
    imdb_request_delay_max_seconds: float = 30
    imdb_api_type: ImdbApiType = ImdbApiType.DOUBAN_HTML
    imdb_cache_ttl_id_not_found_seconds: float = 3600
    proxy_address: str | None = None
    bootstrap_interval_seconds: float = 3600 * 24
    bootstrap_list_interval_seconds: float = 30
    bootstrap_lists_max: int = 100
    douban_rate_limit_delay_seconds: float = 3600
    sync_imdb_cache_interval_seconds: float = 3600
    sync_imdb_cache_to: List[str] = []
    apikey: str | None = None


app_config = AppConfig(_env_prefix="DOUDARR_")
