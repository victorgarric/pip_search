from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version


def check_version(package: str) -> str | None:
    try:
        return pkg_version(package)
    except PackageNotFoundError:
        return False
