import gzip
import io
import unittest
import urllib.error

from cartrack import fetch


class Answer(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def http_error(code):
    return urllib.error.HTTPError("https://example.com/", code, "x", {}, io.BytesIO(b""))


class Get(unittest.TestCase):
    def test_returns_the_body_unzipped(self):
        body = fetch.get("https://example.com/", opener=lambda request, timeout: Answer(gzip.compress(b"hello")))
        self.assertEqual(body, b"hello")

    def test_sends_the_trackers_own_name(self):
        seen = []

        def opener(request, timeout):
            seen.append(request.get_header("User-agent"))
            return Answer(b"ok")
        fetch.get("https://example.com/", opener=opener)
        self.assertTrue(seen[0].startswith("cartrack/"))
        self.assertNotIn("python-urllib", seen[0].lower())     # Carsforsale sites answer that word with a false 500

    def test_data_makes_it_a_post(self):
        seen = []

        def opener(request, timeout):
            seen.append((request.get_method(), request.data))
            return Answer(b"ok")
        fetch.get("https://example.com/", data=b"a=1", opener=opener)
        self.assertEqual(seen, [("POST", b"a=1")])

    def test_a_404_is_gone_and_is_not_retried(self):
        calls = []

        def opener(request, timeout):
            calls.append(1)
            raise http_error(404)
        with self.assertRaises(fetch.Gone):
            fetch.get("https://example.com/", opener=opener, sleep=lambda seconds: None)
        self.assertEqual(len(calls), 1)

    def test_a_429_is_rate_limited(self):
        def opener(request, timeout):
            raise http_error(429)
        with self.assertRaises(fetch.RateLimited):
            fetch.get("https://example.com/", opener=opener, sleep=lambda seconds: None)

    def test_a_failure_is_tried_again_and_then_raised(self):
        calls = []

        def opener(request, timeout):
            calls.append(1)
            raise http_error(503)
        with self.assertRaises(urllib.error.HTTPError):
            fetch.get("https://example.com/", opener=opener, sleep=lambda seconds: None)
        self.assertEqual(len(calls), 3)


class Paced(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.slept = []

        def sleep(seconds):
            self.slept.append(round(seconds, 1))
            self.now += seconds
        self.get = fetch.paced(lambda url, **options: url.encode(), delay=3, clock=lambda: self.now, sleep=sleep)

    def test_the_first_request_to_a_site_does_not_wait(self):
        self.get("https://a.example/1")
        self.assertEqual(self.slept, [])

    def test_the_next_request_to_the_same_site_waits_out_the_delay(self):
        self.get("https://a.example/1")
        self.now += 1
        self.get("https://a.example/2")
        self.assertEqual(self.slept, [2.0])

    def test_another_site_does_not_wait(self):
        self.get("https://a.example/1")
        self.get("https://b.example/1")
        self.assertEqual(self.slept, [])

    def test_it_hands_back_what_the_fetch_gave(self):
        self.assertEqual(self.get("https://a.example/1"), b"https://a.example/1")


if __name__ == "__main__":
    unittest.main()
