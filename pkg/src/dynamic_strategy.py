from typing import final
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from pkg.src.serp_scraper import SerpResult
from pkg.src.strategy_protocol import Strategy

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


@final
class DynamicStrategy(Strategy[SerpResult]):
    def __init__(self):
        pass

    def prepare(self, html: bytes) -> BeautifulSoup:
        return self._hydrate_in_headless_browser(html)

    def finalize(self, serp_result: SerpResult) -> SerpResult:
        return serp_result

    def _hydrate_in_headless_browser(self, b_html: bytes) -> BeautifulSoup:
        html = b_html.decode("utf-8", "replace")
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1200,2400")
        with webdriver.Chrome(options=opts) as d:
            d.get("about:blank")
            d.execute_cdp_cmd("Page.enable", {})
            fid = d.execute_cdp_cmd("Page.getFrameTree", {})["frameTree"]["frame"]["id"]
            d.execute_cdp_cmd("Page.setDocumentContent", {"frameId": fid, "html": html})
            WebDriverWait(d, 10).until(
                lambda x: d.execute_script("return document.readyState") == "complete"
            )
            for _ in range(12):
                d.execute_script(
                    "window.scrollBy(0, 900);window.dispatchEvent(new Event('scroll'))"
                )
            WebDriverWait(d, 10).until(
                lambda x: d.execute_script(
                    "return Array.from(document.images).every(i=>i.complete||i.currentSrc||i.srcset||i.src)"
                )
            )
            out = d.execute_script("return document.documentElement.outerHTML")
        return BeautifulSoup(out, "html.parser")
