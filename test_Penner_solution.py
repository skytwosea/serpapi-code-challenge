import pytest
import bs4


from Penner_solution import (
    MockRequests,
    # MockResponse,
    SerpScraper,
    ScraperTarget,
    ItemTags
)


@pytest.fixture
def mock_get():
    return MockRequests.get()


def test_mock_headers(mock_get):
    headers = mock_get.headers
    assert headers["Content-Type"] == "text/html; charset=ISO-8859-1"
    assert headers["Content-Encoding"] == "gzip"
    assert headers["Cache-Control"] == "private"

def test_is_challenge_input_init_is_valid(mock_get):
    content = mock_get.content
    scraper = SerpScraper(content, ScraperTarget.PAINTERS)
    assert scraper._choice == 1
    assert isinstance(scraper._soup, bs4.BeautifulSoup)
    assert scraper._target_scraper == scraper._painter_scraper
    assert isinstance(scraper._tag_ids, ItemTags)
    assert scraper._validate()
