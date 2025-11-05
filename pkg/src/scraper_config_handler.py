import json
from pathlib import Path
from typing import Any, Self, ClassVar
from dataclasses import dataclass, fields
from importlib.resources.abc import Traversable

from pkg import FILES
from pkg.src.errors import ScraperConfigHandlerError

"""ScraperConfigHandler module: scraper configuration I/O

This module's design is very similar to the design of the
mock_requests module; they perform similar tasks. There is
potential to abstract these two modules.

Initialization
--------------
You may choose to initialize by supplying a valid configuration
mapping to the ScraperConfigHandler class.

Use default values by calling the classmethod constructor
ScraperConfigHandler.from_defaults()

Load any valid JSON file with ScraperConfigHandler.read(path)

Defaults
--------
ScraperConfigHandler default is defined by a class attribute,
which points to a file stored in pkg/files

These class attributes are private. They can be modified by
invoking ScraperConfigHandler.set_default_filename(filename)

The class constructors read() and from_defaults() delegate to
the private method _reader(). For testing, the filepath root
can be changed by invoking this method directly.

ScraperConfigHandler._set() is available as a testing tool for
post-initialization changes to __slot__ attributes

Options Method
--------------
ScraperConfigHandler.options() accepts no arguments. It returns
a tuple of the keys in the read-in config file, which define
the set of available (== implemented) configuration options.

Select Method
-------------
ScraperConfigHandler.select() accepts a single string as argument,
which must be a valid configuration key. This key will select the
correct dict object from the loaded configuration file contents,
create a TargetConfig object, and return it.

Example
-------
>>> from pkg.src.scraper_config_handler import ScraperConfigHandler
>>> config = ScraperConfigHandler.from_defaults()
>>> target = config.select("famous_painters")
"""


def _defaults_root() -> Traversable:
    return FILES


@dataclass(frozen=True, slots=True)
class TargetConfig:
    group_name: str
    tiles_tag_class: str
    tiles_tag_attr: str
    item_tag_class: str
    name_tag_class: str
    year_tag_class: str
    image_tag_class: str


class ScraperConfigHandler:
    _config_default_filename: ClassVar[str] = "config.json"

    __slots__ = [
        "_config",
    ]

    def __init__(self, *, config: dict[str, Any]):
        self._config = config

    @classmethod
    def read(cls: type[Self], config_source_path: Path) -> Self:
        """Read in configuration options from default file or provided Path.

        If invoked with no argument, read() loads a default JSON
        configuration file.
        """
        assert config_source_path.exists()
        _dir = config_source_path.parent
        _name = config_source_path.name
        return cls._reader(_root=_dir, _fname=_name)

    @classmethod
    def from_defaults(cls: type[Self]) -> Self:
        _root = _defaults_root()
        assert _root.is_dir()
        return cls._reader(_root=_root, _fname=cls._config_default_filename)

    @classmethod
    def _reader(
        cls: type[Self],
        *,
        _root: Path | Traversable,
        _fname: str,
    ) -> Self:
        try:
            config_text = _root.joinpath(_fname).read_text()
            config = json.loads(config_text)
        except json.JSONDecodeError as e:
            raise ScraperConfigHandlerError(
                f"Could not parse json payload: {_fname}"
            ) from e
        except (FileNotFoundError, UnboundLocalError) as e:
            raise ScraperConfigHandlerError(f"Default file not found\n{str(e)}") from e
        return cls(config=config)

    @property
    def options(self) -> tuple[str, ...]:
        if not self._config:
            raise ScraperConfigHandlerError(
                f"No configuration available. Invoke read() first."
            )
        return tuple(k for k in self._config.keys())

    def select(self, key: str) -> TargetConfig:
        if not self._config:
            raise ScraperConfigHandlerError(
                f"No configuration available. Invoke read() first."
            )
        if not any(key == k for k in self._config.keys()):
            raise ScraperConfigHandlerError(
                f"key {key} is not an available configuration.\n"
            )
        target_map = self._config[key]
        try:
            _mapped = {f: target_map[f] for f in (f.name for f in fields(TargetConfig))}
            return TargetConfig(**_mapped)
        except KeyError as e:
            raise ScraperConfigHandlerError(
                f"Invalid configuration for {key}: required attribute missing.\n"
            ) from e

    @classmethod
    def _set_default_filename(
        cls,
        *,
        config_filename: str | None = None,
    ) -> None:
        """Class setter for changing default filenames prior to initialization"""
        if config_filename:
            cls._config_default_filename = config_filename

    def _set(self, attr: str, val: Any) -> None:
        """Surgical setter is supplied just in case"""
        assert attr in self.__slots__
        setattr(self, attr, val)
