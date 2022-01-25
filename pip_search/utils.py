from typing import Union

try:
    from importlib.metadata import PackageNotFoundError, distribution
except ImportError:
    from pkg_resources import DistributionNotFound as PackageNotFoundError
    from pkg_resources import get_distribution as distribution


def check_version(package_name: str) -> Union[str, bool]:
    """Check if package is installed and return version.

    Returns:
        str | boll: Version of package if installed, False otherwise.
    """
    try:
        installed = distribution(package_name)
    except PackageNotFoundError:
        return False
    else:
        return installed.version
