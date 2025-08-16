import asyncio
import httpx
from typing import Optional

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class HttpClient:
    def __init__(self, timeout: float = 20.0, rate_limit_per_host: float = 1.0) -> None:
        self.client = httpx.Client(timeout=timeout, headers=DEFAULT_HEADERS, follow_redirects=True)
        self.rate_limit_per_host = rate_limit_per_host
        self._host_locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, host: str) -> asyncio.Lock:
        if host not in self._host_locks:
            self._host_locks[host] = asyncio.Lock()
        return self._host_locks[host]

    def get(self, url: str) -> httpx.Response:
        resp = self.client.get(url)
        return resp

    def close(self) -> None:
        self.client.close()


def get_http_client() -> HttpClient:
    return HttpClient()