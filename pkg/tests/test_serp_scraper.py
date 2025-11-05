import pytest
from dataclasses import fields
from textwrap import dedent
import json
from pkg import FILES
from bs4 import BeautifulSoup

from pkg.src.scraper_config_handler import ScraperConfigHandler
from pkg.src.serp_scraper import (
    SerpItem,
    SerpResult,
    SerpScraper,
)
from pkg.src.strategy_protocol import Strategy


@pytest.fixture
def serp_item():
    return SerpItem(
        rank=0,
        name="this",
        extensions=["here"],
        link="is",
        img_id="a",
        image="test",
    )


@pytest.fixture
def si_map():
    return {"name": "this", "extensions": ["here"], "link": "is", "image": "test"}


@pytest.fixture
def sr_json():
    return dedent("""\
    {
      "TestName": [
        {
          "name": "this",
          "extensions": [
            "here"
          ],
          "link": "is",
          "image": "test"
        }
      ]
    }
    """)


@pytest.fixture
def html_as_bytes():
    return FILES.joinpath("injection_script_example.html").read_bytes()


def test_SerpItem_fields(serp_item):
    assert serp_item._fields() == [f.name for f in fields(SerpItem)]
    exclusions = ["extensions", "name"]
    assert serp_item._fields(exclude=exclusions) == [
        f.name for f in fields(SerpItem) if f.name not in exclusions
    ]


def test_SerpItem_to_map(serp_item, si_map):
    assert serp_item.to_map() == si_map


def test_SerpResult_to_json(serp_item, sr_json):
    sr = SerpResult(
        name="TestName",
        items=[serp_item],
    )
    assert sr.to_json() == json.dumps(json.loads(sr_json), indent=2) + "\n"


def test_expect_tag(html_as_bytes):
    soup = BeautifulSoup(html_as_bytes, "html.parser")
    script_tag = soup.find("script")
    assert script_tag is not None  # make pyright happy
    script_text = script_tag.get_text()

    ScraperConfigHandler._set_default_filename(config_filename="config.json")
    tgt = ScraperConfigHandler.from_defaults().select("famous_painters")
    scraper = SerpScraper(config=tgt, strategy=None)  # TODO: improve this test
    assert scraper._expect_tag(script_tag) == script_tag
    with pytest.raises(TypeError):
        scraper._expect_tag(script_text)
