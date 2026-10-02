from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.response import addinfourl
import pytest
from f2m.core.exceptions import F2MNetworkError
from f2m.net.client import HttpClient


class MockOpener:
    def __init__(self, responses: list):
        self.responses = list(responses)
        self.call_history = []

    def open(self, req, timeout=25):
        url = req.full_url
        self.call_history.append((url, timeout))
        if not self.responses:
            raise URLError("Connection refused")
        resp = self.responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        if isinstance(resp, str):
            fp = BytesIO(resp.encode("utf-8"))
            headers = {"content-type": "text/html"}
            return addinfourl(fp, headers, url, code=200)
        return resp


def test_http_client_success():
    client = HttpClient("https://primary.top")
    mock_opener = MockOpener(["<html><body>OK</body></html>"])
    client._opener = mock_opener

    content = client.fetch("/")
    assert content == "<html><body>OK</body></html>"
    assert len(mock_opener.call_history) == 1
    assert mock_opener.call_history[0][0] == "https://primary.top/"


def test_http_client_bounded_retries():
    client = HttpClient("https://primary.top", max_retries=2, backoff_factor=0.01)
    # Fail twice with 503, then succeed on 3rd attempt
    err1 = HTTPError("https://primary.top/", 503, "Service Unavailable", {}, None)
    err2 = HTTPError("https://primary.top/", 503, "Service Unavailable", {}, None)
    success = "<html>Success on 3rd attempt</html>"

    mock_opener = MockOpener([err1, err2, success])
    client._opener = mock_opener

    content = client.fetch("/")
    assert "Success on 3rd attempt" in content
    assert len(mock_opener.call_history) == 3


def test_http_client_mirror_failover():
    client = HttpClient(
        "https://primary.top",
        mirrors=["https://mirror1.top", "https://mirror2.top"],
        max_retries=1,
        backoff_factor=0.01,
    )
    # Primary fails with 404, mirror1 fails with 503 x 2, mirror2 succeeds
    err_prim = HTTPError("https://primary.top/test", 404, "Not Found", {}, None)
    err_m1_a = HTTPError("https://mirror1.top/test", 503, "Unavailable", {}, None)
    err_m1_b = HTTPError("https://mirror1.top/test", 503, "Unavailable", {}, None)
    success = "<html>Mirror2 OK</html>"

    mock_opener = MockOpener([err_prim, err_m1_a, err_m1_b, success])
    client._opener = mock_opener

    content = client.fetch("/test")
    assert "Mirror2 OK" in content
    called_urls = [u for u, _ in mock_opener.call_history]
    assert "https://primary.top/test" in called_urls
    assert "https://mirror1.top/test" in called_urls
    assert "https://mirror2.top/test" in called_urls


def test_http_client_exhaustion_raises_f2m_network_error():
    client = HttpClient("https://primary.top", mirrors=["https://m.top"], max_retries=0)
    mock_opener = MockOpener([
        HTTPError("https://primary.top/", 500, "Error", {}, None),
        URLError("Connection reset"),
    ])
    client._opener = mock_opener

    with pytest.raises(F2MNetworkError, match="Could not reach https://primary.top"):
        client.fetch("/")


def test_session_transient_redirect():
    client = HttpClient("https://old-f2m.top")

    # Mock response with redirected URL
    fp = BytesIO(b"Redirected content")
    headers = {"content-type": "text/html"}
    resp = addinfourl(fp, headers, "https://new-f2m.top/home/", code=200)

    mock_opener = MockOpener([resp])
    client._opener = mock_opener

    assert client.current_base_url == "https://old-f2m.top"
    client.fetch("/")
    # In-memory session updated to new domain
    assert client.current_base_url == "https://new-f2m.top"
