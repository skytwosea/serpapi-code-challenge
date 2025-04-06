import json
from dataclasses import dataclass
from bs4 import BeautifulSoup as bs
import sys


@dataclass
class MockResponse:
    """Mock response object; simulates return from requests.get"""
    status_code: int
    headers: dict
    content: bytes


class MockRequests:
    """Mock requests class; simulates get functionality from requests library"""
    def __init__(self):
        pass

    @staticmethod
    def get() -> MockResponse:
        try:
            with open("files/van-gogh-paintings-search-header.json", "r") as f:
                mock_headers = json.load(f)
            with open("files/van-gogh-paintings.html", "r") as f:
                mock_content = f.read()
        except FileNotFoundError as e:
            print(
                "FileNotFoundError:\n"
                "One of the header-mock json or content-mock html files\n"
                "can't be found. Check that the directory containing this\n"
                "script contains the following:\n"
                "  files/van-gogh-paintings-search-header.json\n"
                "  files/van-gogh-paintings.html"
            )
            sys.exit(1)

        return MockResponse(
            status_code = 200,
            headers = mock_headers,
            content = mock_content.encode("utf-8"),
        )


class FamousPainters:
    """Scraper class with parameters targeted to SERP data for Google's famous painters layout
    
    Searches for famous painters such as Salvador Dali, Rembrandt, and Van Gogh are laid out
    uniquely compared to searches for painters that are not (yet) well known.

    The HTML source that describes the grid-panel of paintings is grouped within a div tag
    with the following class designator:
        xfX4Ac JI5uCe qB9BY yWNJXb qzPQNd

    Each individual painting as a clickable icon is contained within a div tag with the
    following class designator:
        iELo6

    We can first check that the grid-panel tag exists; if it does not, then we are looking
    at a SERP for something other than a famous painter's results. If it is found, then we
    create a generator for all div classes denoted by the single-painting designator, and
    scrape each for the requisite information.
    """

    _famous_grid_tag = {
        "class": "wDYxhc",
        "data-attrid": "kc:/visual_art/visual_artist:works",
        "data-md": "467",
        "data-hveid": "CDMQAA",
    }
    _famous_single_name = "iELo6"
    _parser = "html.parser"  # BeautifulSoup html parser designator


    def __init__(self, src: bytes):
        self.soup = bs(src, self._parser)
        self.is_valid = self._check_for_famous_grid()

    def _check_for_famous_grid(self) -> bool:
        """Check if this search can be handled by this class"""
        panel_div = self.soup.find("div", self._famous_grid_tag)
        if not panel_div:
            return False
        return True

    def scrape(self) -> bool:
        """Validate input, then orchestrate scrape of requisite information"""
        if not self.is_valid:
            return False

        grid_iterator = (tag for tag in self.soup.find_all("div", {"class":self._famous_single_name}))

        # TODO: complete me

        return False
