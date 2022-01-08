try:
    from importlib.metadata import PackageNotFoundError, distribution
except ImportError:
    from pkg_resources import DistributionNotFound as PackageNotFoundError
    from pkg_resources import get_distribution as distribution


def check_version(package: str) -> str | bool:
    """Check if package is installed and return version."""
    try:
        installed = distribution(package)
    except PackageNotFoundError:
        return False
    else:
        return installed.version
