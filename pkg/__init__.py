from importlib import resources
from importlib.resources.abc import Traversable
from typing import Final

"""Package initialization for pkg

FILES: an importable reference to the pkg/files directory
provides access to configuration and data files to any
module that imports it.

While it is marked Final for type checking, there is no
runtime check on its modification.
"""

FILES: Final[Traversable] = resources.files("pkg.files")