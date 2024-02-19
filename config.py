from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    cache_base_dir: str = "cache"
    collection_request_delay_max: float = 0.1
    collection_cache_ttl: float = 3600
    imdb_request_delay_max: float = 1.0


app_config = AppConfig(_env_prefix="DOUDARR_")
