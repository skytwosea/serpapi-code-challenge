from importlib import resources
from importlib.resources.abc import Traversable
from typing import Final

"""Package initialization for pkg

FILES: an importable reference to the pkg/ref directory
provides access to configuration and reference files to
any module that imports it.
"""

FILES: Final[Traversable] = resources.files("pkg.ref")
