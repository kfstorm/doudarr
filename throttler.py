from collections import defaultdict
import time
import httpx

from config import app_config


class Throttler:
    def __init__(self):
        self.next_call_time = defaultdict(float)

    async def _on_request(self, request: httpx.Request):
        next_call_time = self.next_call_time[request.url.host]
        now = time.time()
        if now < next_call_time:
            raise Exception(
                f"Rate limited. Need to wait at least {next_call_time - now}"
                + f" seconds before the next call to {request.url.host}."
            )

    async def _on_response(self, response: httpx.Response):
        if response.status_code == 302 and "sec.douban.com" in response.headers.get(
            "location"
        ):
            # Rate limited.
            self.next_call_time[response.url.host] = (
                time.time() + app_config.douban_rate_limit_delay_seconds
            )
            raise Exception(
                "Rate limited. Need to wait at least "
                + str(app_config.douban_rate_limit_delay_seconds)
                + " seconds before the next call."
            )

    def get_event_hooks(self):
        return {
            "request": [self._on_request],
            "response": [self._on_response],
        }

    def get_info(self):
        now = time.time()
        return {
            key: {
                "is_rate_limited": now < value,
                "wait_time": max(0, value - now),
            }
            for key, value in self.next_call_time.items()
        }


throttler = Throttler()
