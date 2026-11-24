"""Open the editor from its file URL or a loopback HTTP test server."""
import os
from pathlib import Path
from urllib.parse import urljoin


def editor_url():
    return os.environ.get("KARTA_TEST_URL") or Path(__file__).with_name("Karta-2.1.html").as_uri()


def roundtrip_url(page, download):
    if not os.environ.get("KARTA_TEST_URL"):
        return download.as_uri()
    url = urljoin(editor_url(), "test-roundtrip.html")
    page.route(url, lambda route: route.fulfill(path=download, content_type="text/html; charset=utf-8"))
    return url
