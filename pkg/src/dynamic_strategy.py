from bs4 import BeautifulSoup
from pkg.src.serp_scraper import SerpResult

"""
This module implements a strategy for the Strategy protocol
defined in pkg.src.strategy_protocol

In pkg.src.serp_scraper, there are two ways we can handle the
problem of URL injection via js scripts: statically, by scraping
the page's scripts and extracting the data we need, or dynamically,
by rendering the html in a headless browser and skipping the need
for script surgery. The Strategy protocol accomodates both options
and leaves the choice to the caller.

Here, we implement the dynamic approach.

prepare() is expected to render the provided html using a headless
browser such as Selenium, and go through the steps that are needed
so that the soup that is returned to SerpScraper can be scraped
for the correct URLs throughout.

finalize() is not currently expected to do anything. It should
return what it has been passed.
"""

class DynamicStrategy:
    
    def __init__(self):
        pass

    def prepare(self, html: bytes) -> BeautifulSoup:
        ...

    def finalize(self, intermediate: SerpResult) -> SerpResult:
        ...
