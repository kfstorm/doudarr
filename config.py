from enum import Enum
from pydantic_settings import BaseSettings


class ImdbApiType(str, Enum):
    DOUBAN_HTML = "DOUBAN_HTML"


class AppConfig(BaseSettings):
    cache_base_dir: str = "cache"
    collection_request_delay_max: float = 0.1
    collection_cache_ttl: float = 3600
    imdb_request_delay_max: float = 1.0
    imdb_api_type: ImdbApiType = ImdbApiType.DOUBAN_HTML
    imdb_cache_ttl_id_not_found: float = 3600
    proxy_address: str | None = None


app_config = AppConfig(_env_prefix="DOUDARR_")
