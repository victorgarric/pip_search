try:
    from importlib.metadata import PackageNotFoundError, distribution
except ImportError:
    from pkg_resources import DistributionNotFound as PackageNotFoundError
    from pkg_resources import get_distribution as distribution


def check_version(package: str):
    try:
        return distribution(package).version
    except PackageNotFoundError:
        return False
