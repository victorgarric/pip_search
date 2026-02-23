from importlib.metadata import PackageNotFoundError, version
from typing import Final

try:
    __version__ = version("pip_search")
except PackageNotFoundError:
    __version__: Final[str] = "dev"
