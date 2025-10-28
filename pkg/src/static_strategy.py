# from __future__ import annotations
from dataclasses import dataclass, fields
from bs4 import BeautifulSoup
# from bs4.filter import SoupStrainer
from bs4.element import Tag, ResultSet
from typing import ClassVar, Any, Generator, Mapping
# from enum import StrEnum
# import re
import json
# from importlib.abc import Traversable
from pkg.src.scraper_config_handler import TargetConfig
import esprima
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

Here, we implement the static approach.

prepare() leaves the html unaltered and unrendered. It
initializes a BeautifulSoup object and returns it with no
modifications. It also returns a mapping of image ID values
to URLs, which is created by scraping, filtering, and parsing
the <script/ tags in the soup.

finalize() takes the SerpResult object produced by the
call to SerpScraper.scrape() and edits the list of SerpItems
via the map.
"""


class StaticStrategy:

    def __init__(self):
        self.edits_map: dict[str, str]|None = None

    def prepare(self, html: bytes) -> BeautifulSoup:
        # set self.edits_map before returning soup!
        ...

    def finalize(self, intermediate: SerpResult) -> SerpResult:
        ...

    def _inject_valid_urls(self, partial: SerpResult, mapping: dict[str, str]) -> None:
        for tile in partial.items:
            tile.image = mapping[tile.img_id]

    def _quickcheck(self, text):
        return "_setImagesSrc(ii,s,r)" in text

    def _parse_js(self, text: str) -> esprima.nodes.Script:
        return esprima.parseScript(text)

    def _get_var_decls(self, parsed: esprima.nodes.Script) -> list[esprima.nodes.VariableDeclaration]:
        return [node for node in self._traverse_js_ast(parsed)]

    def _traverse_js_ast(self, obj: Any) -> Generator[esprima.nodes.VariableDeclaration, Any, Any]:
        try:
            if not obj or any(isinstance(obj, T) for T in [str, bool]):
                return
            if isinstance(obj, list):
                for item in obj:
                    yield from self._traverse_js_ast(item)
            if obj.type == "VariableDeclaration":
                yield obj
            for field in obj.__dir__():
                yield from self._traverse_js_ast(getattr(obj, field))
        except Exception:
            # not the kind of js function we're looking for
            return

    def _build_injected_urls_map(self, soup: BeautifulSoup) -> dict[str, str]:
        """
        _L_FkZ4qlAtyDwbkP49Pj0QU_63

        The string above is an image id, found in each artwork tile (each with a
        similar/same body and different numeric suffix, following the last
        underscore). It links three objects in the html document:
            - the artwork div tile that we are scraping
            - a div tag that links to a bullshit placeholder URL
            - a script tag that contains a js function with variable declarations,
              one of which is that id and another is the true URL we are looking for
        The scraper needs to do two scraping and parsing steps:
            (1)
            - extract the name/extensions/link data from each tile, as we already are
            - instead of getting the wrong URL, capture that weird id code from each
              tile and save it as an attribute for each SerpItem object
            (2)
            - extract all script tags
            - parse the js functions using esprima or another library, and store all
              variable declarations in a map
            - if the map contains one of those id tags (test against a set), then
              save that id number and its corresponding crazy URL in an object. Might
              need to lop off the _L_ prefix of the id value; I'm not sure that all
              of the scripts will have it.
        From the above two steps, we should end up with the same number of SerpItem
        objects as we have url redirect map items. Using the id number mapping, store
        the crazy URL in the corresponding SerpItem object.
        """
        scripts = [
            script.get_text() for script in
            soup.find_all("script")
        ]
        scripts = list(filter(self._quickcheck, scripts))
        img_url_map = {}
        for script in scripts:
            ast = self._parse_js(script)
            var_declarations = self._get_var_decls(ast)
            mapping = self._extract_values_from_declarations(var_declarations)
            img_url_map.update(mapping)
        return img_url_map

    def _extract_values_from_declarations(
        self,
        decls: list[esprima.nodes.VariableDeclaration]
    ) -> dict:
        s = ""
        ii = ""
        for decl in decls:
            if decl.type == "ExpressionStatement":
                continue
            if decl.declarations[0].id.name == "r":
                continue
            elif decl.declarations[0].id.name == "s":
                s = decl.declarations[0].init.value
            elif decl.declarations[0].id.name == "ii":
                ii = decl.declarations[0].init.value
        return {ii:s}