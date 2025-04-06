import pytest


from Penner_solution import (
    MockRequests,
    MockResponse,
    FamousPainters,
)


@pytest.fixture
def mock_get():
    return MockRequests.get()


def test_mock_headers(mock_get):
    headers = mock_get.headers
    assert headers["Content-Type"] == "text/html; charset=ISO-8859-1"
    assert headers["Content-Encoding"] == "gzip"
    assert headers["Cache-Control"] == "private"

def test_is_challenge_input_valid(mock_get):
    content = mock_get.content
    fp_init = FamousPainters(content)
    assert fp_init.is_valid
