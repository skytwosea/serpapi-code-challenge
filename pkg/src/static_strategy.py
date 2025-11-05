import re
import esprima
from typing import final
from bs4 import BeautifulSoup
from esprima.visitor import Visitor

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

Here, we implement the static approach.

prepare() leaves the html unaltered and unrendered. It
initializes a BeautifulSoup object and returns it with no
modifications. It also creates a mapping of image ID values
to URLs, which is created by scraping, filtering, and parsing
the <script/ tags in the soup. This edits map is stored as an
attribute of the StaticStrategy class, and is referenced when
finalize() is invoked.

finalize() takes the SerpResult object produced by the
call to SerpScraper.scrape() and edits the list of SerpItems
via the map.
"""

_RE_FN_PATTERN = re.compile(
    r"_setImagesSrc\s*"
    r"\(\s*(\b(?:ii|r|s)\b)\s*,\s*"
    r"(?!\1)(\b(?:ii|r|s)\b)\s*,\s*"
    r"(?!\1|\2)(\b(?:ii|r|s)\b)\s*\)"
)


@final
class StaticStrategy(Strategy[SerpResult]):
    def __init__(self):
        self.edits_map: dict[str, str] | None = None

    def prepare(self, html: bytes) -> BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        self.edits_map = self._build_edits_map(soup)
        return soup

    def finalize(self, serp_result: SerpResult) -> SerpResult:
        assert self.edits_map is not None
        for item in serp_result.items:
            item.image = self.edits_map.get(item.img_id, item.image)
        return serp_result

    def _inject_valid_urls(self, partial: SerpResult, mapping: dict[str, str]) -> None:
        for tile in partial.items:
            tile.image = mapping[tile.img_id]

    def _quickcheck(self, text) -> bool:
        return bool(_RE_FN_PATTERN.search(text))

    def _build_edits_map(self, soup: BeautifulSoup) -> dict[str, str]:
        all_scripts = [
            s.get_text()
            for s in soup.find_all("script")
            if self._quickcheck(s.get_text())
        ]
        _emap = {}
        for script in all_scripts:
            _emap.update(self._extract_script_vars(str(script)))
        return _emap

    def _extract_script_vars(self, text: str) -> dict[str, str]:
        ast = esprima.parseScript(text)
        v = SrcInjectorVisitor()
        v.visit(ast)  # kicks off recursion
        return {i: v.s_val for i in v.ids if v.s_val}


class SrcInjectorVisitor(Visitor):
    def __init__(self):
        self.s_val: str | None = None
        self.ids: list[str] = []

    def visit_VariableDeclarator(self, node):
        name = getattr(getattr(node, "id", None), "name", None)
        init = getattr(node, "init", None)
        tinit = getattr(init, "type", None)

        assert init is not None  # shush, Pyright...

        if name == "s" and tinit == "Literal" and isinstance(init.value, str):
            self.s_val = init.value

        elif name == "ii" and tinit == "ArrayExpression":
            for el in getattr(init, "elements", []) or []:
                if getattr(el, "type", None) == "Literal" and isinstance(el.value, str):
                    self.ids.append(el.value)

        self.generic_visit(node)
