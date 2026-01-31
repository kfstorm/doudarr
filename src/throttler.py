from collections import defaultdict
import time
import httpx

from .config import app_config


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
        # Douban rate limit detection (302 redirect to sec.douban.com)
        if response.status_code == 302 and "sec.douban.com" in response.headers.get(
            "location", ""
        ):
            wait_time = app_config.douban_rate_limit_delay_seconds
            self.next_call_time[response.url.host] = time.time() + wait_time
            raise Exception(
                f"Rate limited by {response.url.host}. Need to wait at least "
                + f"{wait_time} seconds before the next call."
            )

        # HTTP 429 rate limit detection (standard rate limiting)
        if response.status_code == 429:
            # Try to get wait time from Retry-After header
            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                wait_time = int(retry_after)
            else:
                # Try to calculate from X-RateLimit-Reset header
                reset_time = response.headers.get("X-RateLimit-Reset")
                if reset_time and reset_time.isdigit():
                    wait_time = max(0, int(reset_time) - int(time.time()))
                else:
                    # Default fallback
                    wait_time = 60

            self.next_call_time[response.url.host] = time.time() + wait_time
            raise Exception(
                f"Rate limited by {response.url.host}. Need to wait at least "
                + f"{wait_time} seconds before the next call."
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
