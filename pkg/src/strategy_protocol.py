from typing import Protocol, TypeVar
from bs4 import BeautifulSoup

T_SerpResult = TypeVar("T_SerpResult")  # avoid circular import for typing


class Strategy(Protocol[T_SerpResult]):
    def prepare(self, html: bytes) -> BeautifulSoup: ...
    def finalize(self, serp_result: T_SerpResult) -> T_SerpResult: ...
