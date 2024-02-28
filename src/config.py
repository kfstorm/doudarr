import json
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    cache_base_dir: str = Field("cache", description="缓存路径。默认值为相对路径，也可以填写绝对路径。")
    douban_api_request_delay_max_seconds: float = Field(
        1,
        description="请求豆瓣API时的最大延迟（秒）。两次请求之间的延迟是随机的，这里配置的是最大值。",
    )
    list_cache_ttl_seconds: float = Field(
        3600 * 24,
        description="列表缓存的TTL（秒）。列表缓存会在一段时间后过期，过期后会重新抓取。如果豆瓣列表的条目有更新，重新抓取后会拿到最新的条目。",
    )
    imdb_request_delay_max_seconds: float = Field(
        30,
        description="抓取IMDb信息时的最大延迟（秒）。两次请求之间的延迟是随机的，这里配置的是最大值。",
    )
    imdb_cache_ttl_id_not_found_seconds: float = Field(
        3600 * 24,
        description="IMDb ID未找到时的缓存TTL（秒）。"
        + "部分豆瓣条目没有IMDb ID（可能是暂时的），没有找到时会缓存一段时间，避免重复查询。TTL到期后会再次查询。",
    )
    proxy_address: str | None = Field(None, description="代理地址，所有HTTP请求将通过代理转发。")
    bootstrap_interval_seconds: float = Field(
        3600 * 24,
        description="缓存预热的时间间隔（秒）。"
        + "缓存预热会在后台定期执行，用于抓取IMDb信息并缓存，加快后续查询速度。设置间隔可以避免短时间内抓取太多信息，导致访问受限。",
    )
    bootstrap_list_interval_seconds: float = Field(
        30,
        description="缓存预热时抓取两个列表之间的时间间隔（秒）。设置间隔可以避免短时间内抓取太多列表，导致访问受限。",
    )
    bootstrap_lists_max: int = Field(
        100,
        description="缓存预热时抓取的列表最大数量。每次缓存预热只会抓取部分列表，这个值越大，抓取的列表数量越多，IMDb信息的预热越充分。",
    )
    douban_rate_limit_delay_seconds: float = Field(
        3600,
        description="豆瓣API的速率限制延迟（秒）。当遇到豆瓣API返回访问限制时，在配置的时间范围内不再请求豆瓣API，避免访问受限更严重。",
    )
    apikey: str | None = Field(
        None,
        description="API密钥。API密钥用于对外提供访问权限，部分API只有在提供了正确的API密钥时才能访问，例如`/sync` API。",
    )
    sync_imdb_cache_interval_seconds: float = Field(
        3600,
        description="同步IMDb缓存到其他Doudarr实例的时间间隔（秒）。"
        + "同步IMDb缓存会定期将缓存同步到其他Doudarr实例上，以便多个Doudarr实例之间共享IMDb缓存。",
    )
    sync_imdb_cache_to: List[str] = Field(
        [],
        description="同步IMDb缓存到其他Doudarr实例的URL列表。同步IMDb缓存会定期将缓存同步到其他Doudarr实例上，"
        + "以便多个Doudarr实例之间共享IMDb缓存。该参数可以包括多个URL，用于同步到多个Doudarr实例。参数示例：`"
        + json.dumps(
            [
                f"http://doudarr-another-{i}:8000/sync?apikey=another-apikey-{i}"
                for i in range(1, 3)
            ]
        )
        + "`。注意这里的apikey需要填写对应实例的apikey，而不是自己的。该参数的值较为复杂，配置环境变量时注意转义。",
    )
    cookie_douban_com_dbcl2: str | None = Field(
        None,
        description="豆瓣网站的cookie中key为`dbcl2` cookie的值。"
        + "如果想让Doudarr以登录用户的身份去访问豆瓣的接口，请配置该参数。",
    )


app_config = AppConfig(_env_prefix="DOUDARR_")
