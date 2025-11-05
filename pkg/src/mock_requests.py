import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Self, ClassVar
from importlib.resources.abc import Traversable

from pkg import FILES
from pkg.src.errors import MockRequestsError

"""MockRequests module: simple mocking for requests.get functionality

This module's design is very similar to the design of the
scraper_config_handler module; they perform similar tasks.
There is potential to abstract these two modules.

Initialization
--------------
You may choose to initialize by supplying valid header,
content, and optional status_code parameters to the
MockRequests class.

Use default values by calling the classmethod constructor
MockRequests.from_defaults()

Load any valid header (JSON) and/or content (bytes) files
with MockRequests.read(path, path)

Defaults
--------
MockRequests defaults are defined by two class
attributes, which point to files stored in pkg/files

These class attributes are private. They can be modified by
invoking MockRequests._set_default_filenames(filename, filename)

The class constructors read() and from_defaults() delegate to
the private constructor _reader(). For testing, the filepath root
can be changed by invoking this method directly.

MockRequests._set() is available as a testing tool for
post-initialization changes to __slot__ attributes

Get Method
----------
MockRequests.get() can accept any number of args or kwargs,
but does not use them. This is so the mock get function
can be used as a drop-in, temporary replacement for the
real requests.get()... if you ever wanted to do such a thing.

Example
-------
>>> from pkg.src.mock_requests import MockRequests
>>> mock_req = MockRequests.from_defaults()
>>> response = mock_req.get()
"""


def _defaults_root() -> Traversable:
    return FILES


@dataclass(frozen=True, slots=True)
class MockResponse:
    """Simulates return object from requests.get method call"""

    header: dict[str, Any]
    content: bytes
    status_code: int


class MockRequests:
    """Simulates get functionality from requests library"""

    _header_default_filename: ClassVar[str] = "van-gogh-paintings-search-header.json"
    _content_default_filename: ClassVar[str] = "van-gogh-paintings.html"

    # instance attributes, as slots
    __slots__ = ["_header", "_content", "_status_code"]

    def __init__(
        self,
        *,
        header: dict[str, Any],
        content: bytes,
        status_code: int = 200,
    ):
        self._header = header
        self._content = content
        self._status_code = status_code

    @classmethod
    def read(
        cls: type[Self], header_source_path: Path, content_source_path: Path
    ) -> Self:
        assert header_source_path.exists(), (
            f"header source path not found: {header_source_path}"
        )
        assert content_source_path.exists(), (
            f"content source path not found: {content_source_path}"
        )

        _hdir = header_source_path.parent
        _cdir = content_source_path.parent

        _hname = header_source_path.name
        _cname = content_source_path.name

        return cls._reader(
            _header_root=_hdir,
            _content_root=_cdir,
            _header_name=_hname,
            _content_name=_cname,
        )

    @classmethod
    def from_defaults(cls: type[Self]) -> Self:
        _root = _defaults_root()
        assert _root.is_dir(), (
            f"Exception with default files root: directory not found: {_root}"
        )
        return cls._reader(
            _header_root=_root,
            _content_root=_root,
            _header_name=cls._header_default_filename,
            _content_name=cls._content_default_filename,
        )

    @classmethod
    def _reader(
        cls: type[Self],
        *,
        _header_root: Path | Traversable,
        _content_root: Path | Traversable,
        _header_name: str,
        _content_name: str,
    ) -> Self:
        """Constructor that uses package default data

        Default data source is found at pkg/ref
        """
        try:
            header_text = _header_root.joinpath(_header_name).read_text(
                encoding="utf-8"
            )
            header = json.loads(header_text)
            content = _content_root.joinpath(_content_name).read_bytes()
        except json.JSONDecodeError as e:
            raise MockRequestsError(
                f"Could not parse json payload: {cls._header_default_filename}"
            ) from e
        except (FileNotFoundError, UnboundLocalError) as e:
            raise MockRequestsError(f"Default file not found\n{str(e)}") from e
        return cls(header=header, content=content, status_code=200)

    def get(self, *args, **kwargs) -> MockResponse:
        """Returns a MockResponse object from instance attributes

        This method does not use submitted arguments, but it does accept
        any args/kwargs so that it can be used as a drop-in substitute
        for requests.get()
        """
        if any(getattr(self, attr) is None for attr in self.__slots__):
            bad_attrs = [attr for attr in self.__slots__ if getattr(self, attr) is None]
            raise MockRequestsError(
                f"One or more instance attributes is None\n"
                f"Cannot create a MockResponse object.\n"
                f"Bad attributes: {bad_attrs}"
            )
        return MockResponse(
            header=self._header,
            content=self._content,
            status_code=self._status_code,
        )

    @classmethod
    def _set_default_filenames(
        cls,
        *,
        header_filename: str | None = None,
        content_filename: str | None = None,
    ) -> None:
        """Class setter for changing default filenames prior to initialization"""
        if header_filename:
            cls._header_default_filename = header_filename
        if content_filename:
            cls._content_default_filename = content_filename

    def _set(self, attr: str, val: Any) -> None:
        """Surgical setter is supplied just in case"""
        assert attr in self.__slots__
        setattr(self, attr, val)
