import json
from typing import ClassVar
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
from dataclasses import dataclass, fields

from pkg.src.strategy_protocol import Strategy
from pkg.src.scraper_config_handler import TargetConfig


@dataclass(slots=True)
class SerpItem:
    _exclude: ClassVar[list[str]] = ["rank", "img_id"]

    rank: int
    name: str
    extensions: list[str]
    link: str
    img_id: str
    image: str

    def _fields(self, exclude: list[str] = []) -> list[str]:
        return [f.name for f in fields(self) if f.name not in exclude]

    def to_map(self) -> dict[str, str | list[str]]:
        fieldmap = {
            attr: getattr(self, attr) for attr in self._fields(exclude=self._exclude)
        }
        if not any(str(k).strip() for k in self.extensions):
            fieldmap.pop("extensions", None)
        return fieldmap


@dataclass(frozen=True, slots=True)
class SerpResult:
    name: str
    items: list[SerpItem]

    def to_json(self) -> str:
        payload = {
            self.name: [
                item.to_map() for item in sorted(self.items, key=lambda k: k.rank)
            ]
        }
        dump = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False)
        if not dump.endswith("\n"):
            dump += "\n"
        return dump


class SerpScraper:
    """"""

    def __init__(self, *, config: TargetConfig, strategy: Strategy[SerpResult]):
        self.config = config
        self.strategy = strategy

    def scrape(self, html: bytes) -> SerpResult:
        soup = self.strategy.prepare(html)
        unhydrated = self._extract_via_attrs(soup)
        return self.strategy.finalize(unhydrated)

    def _extract_via_attrs(self, soup: BeautifulSoup) -> SerpResult:
        cfg = self.config
        root = self._expect_tag(soup.find("div", class_=cfg.tiles_tag_class))
        tiles: ResultSet = root.find_all("div", class_=cfg.item_tag_class)
        serp_items = []
        for rank, node in enumerate(tiles):
            _href = node.find("a")
            # TODO: lift this URL prefix out
            link = f"https://www.google.com{_href.get('href', '')}"
            name = node.find(class_=cfg.name_tag_class).get_text()
            year = node.find(class_=cfg.year_tag_class).get_text()
            _img = node.find("img", class_=cfg.image_tag_class)
            img_id = _img.get("id")
            image = _img.get("data-src") or _img.get("src")
            serp_items.append(
                SerpItem(
                    rank=rank,
                    name=name,
                    extensions=[year],
                    link=link,
                    img_id=img_id,
                    image=image,
                )
            )
        return SerpResult(name=cfg.group_name, items=serp_items)

    def _extract_via_selectors(self, soup: BeautifulSoup) -> SerpResult:
        """
        Use CSS selectors instead
        """
        ...

    def _expect_tag(self, element: object) -> Tag:
        # helper to make Pyright stop complaining
        # BeautifulSoup typing is a mess
        if isinstance(element, Tag):
            return element
        raise TypeError(f"element is not of type Tag: {element}")
