import time
import httpx

from config import app_config


class Throttler:
    def __init__(self):
        self.next_call_time = 0

    async def _on_request(self, request: httpx.Request):
        if "douban" in request.url.host:
            now = time.time()
            if now < self.next_call_time:
                raise Exception(
                    "Rate limited. Need to wait at least "
                    + str(self.next_call_time - now)
                    + " seconds before the next call."
                )

    async def _on_response(self, response: httpx.Response):
        if response.status_code == 302 and "sec.douban.com" in response.headers.get(
            "location"
        ):
            # Rate limited.
            self.next_call_time = (
                time.time() + app_config.douban_rate_limit_delay_seconds
            )
            raise Exception(
                "Rate limited. Need to wait at least "
                + str(app_config.douban_rate_limit_delay_seconds)
                + " seconds before the next call."
            )

    def get_client_args(self):
        return {
            "event_hooks": {
                "request": [self._on_request],
                "response": [self._on_response],
            },
        }

    def get_info(self):
        now = time.time()
        return {
            "is_rate_limited": now < self.next_call_time,
            "wait_time": max(0, self.next_call_time - now),
        }


throttler = Throttler()
