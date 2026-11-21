"""Plain HTTP: gzip, a few tries, and clear errors for "gone" and "slow down". After aptrack/fetch.py."""

import gzip
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "cartrack/0.1"


class Gone(Exception):
    """The address answered 404 or 410."""


class RateLimited(Exception):
    """The site answered 429. Callers come back later instead of retrying."""


def get(url, *, timeout=25, tries=3, headers=None, opener=urllib.request.urlopen, sleep=time.sleep, data=None):
    """Fetch `url` and return the body as bytes, decompressed if the server gzipped it.
    `data` (bytes) sends it as a POST."""
    request = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET", headers={
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Encoding": "gzip",
        **(headers or {}),
    })
    for attempt in range(tries):
        try:
            with opener(request, timeout=timeout) as response:
                body = response.read()
            return gzip.decompress(body) if body[:2] == b"\x1f\x8b" else body
        except urllib.error.HTTPError as error:
            error.close()
            if error.code in (404, 410):
                raise Gone(url) from error
            if error.code == 429:
                raise RateLimited(url) from error
            last = error
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as error:
            last = error
        if attempt < tries - 1:
            sleep(2 * (attempt + 1))
    raise last


def paced(get=get, delay=3.0, clock=time.monotonic, sleep=time.sleep):
    """A `get` that keeps requests to the same site at least `delay` seconds apart. Three seconds is the
    crawl delay DealerOn sites ask for in robots.txt."""
    last = {}

    def paced_get(url, **options):
        host = urllib.parse.urlparse(url).netloc
        if host in last:
            wait = last[host] + delay - clock()
            if wait > 0:
                sleep(wait)
        try:
            return get(url, **options)
        finally:
            last[host] = clock()
    return paced_get
