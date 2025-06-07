from typing import Union
import argparse
import glob
import os
import requests
from bs4 import BeautifulSoup
from loguru import logger

try:
    from importlib.metadata import PackageNotFoundError, distribution
except ImportError as e:
    # logger.warning(f"pip_search importlib.metadata module not found: {e} {type(e)}")
    from pkg_resources import DistributionNotFound as PackageNotFoundError
    from pkg_resources import get_distribution as distribution


try:
    from . import __version__
except (ModuleNotFoundError, ImportError) as e:
    # logger.warning(f"pip_search module not found: {e} {type(e)}")
    __version__ = "0.0.0"


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

def read_metafile(distpath):
    name = None
    version = None
    try:
        with open(distpath+'/METADATA') as f:
            meta = f.readlines()[:5]
        for line in meta:
            if 'Name:' in line:
                name = line.split(':')[1].strip()
            if 'Version:' in line:
                version = line.split(':')[1].strip()

    except Exception as e:
        print(f'error reading {distpath}: {e} {type(e)}')
    return name, version, distpath

# : res = [k for k in search(name_list[0],args) if k.name == name_list[0]]

def get_local_libs(libpath):
    alldirs = sorted([k for k in glob.glob(libpath+'**',recursive=False, include_hidden=True) if os.path.isdir(k)])
    dists_found = [k for k in alldirs if os.path.exists(k+'/METADATA')]
    # dists_found = [k for k in glob.glob(libpath+'**',recursive=False, include_hidden=True) if os.path.isdir(k) and 'dist-info' in k and os.path.exists(k+'/METADATA')]
    print(f'alldirs: {len(alldirs)} dists_found: {len(dists_found)} in {libpath}')
    name_list = []
    nodist_list = []
    for dist in dists_found:
        distname,version,distpath = read_metafile(dist)
        if distname:
            name_list.append({'name':distname,'version':version, 'distpath':distpath})
        else:
            print(f'no name found in {dist}')
    # make a list of folders with no METADATA file
    tmplist = sorted([k for k in alldirs if 'dist-info' not in k])
    nodistlist = [k for k in tmplist if k.split('/')[-1] in [x['name'] for x in name_list]]
    nodist_list = [k for k in alldirs if k.split('/')[-1] not in dists_found]
    return name_list

def check_pypi_version(libname):
    baseurl = f'https://pypi.org/project/{libname}'
    pkg_name = None
    pkg_version = None
    session = requests.Session()
    try:
        r = session.get(baseurl)
        soup = BeautifulSoup(r.text, "html.parser")
        # pkgheader = soup.select('h1[class*="package-header__name"]',limit=1)
        pkgheader = soup.select('h1[class*="package-header__name"]',limit=1)
        for p in pkgheader:
            pkg_name,pkg_version = p.text.strip().split(' ')
            return pkg_name, pkg_version
    except Exception as e:
        print(f'error checking {libname}: {e} {type(e)}')
        return None, None


def check_local_libs(libpath):
    local_libs = get_local_libs(libpath)
    outdated_libs = []
    error_list = []
    for lib in local_libs:
        # print(f'checking {lib["name"]}')
        try:
            pypi_name, pypi_version = check_pypi_version(lib["name"])
        except TypeError as e:
            print(f'TypeError checking {lib}: {e}')
            error_list.append(lib)
            continue
        print(f'pypi: {pypi_name} {pypi_version} local: {lib["name"]} {lib["version"]}')
        if pypi_version != lib["version"]:
            print(f'upgrade {lib["name"]} from {lib["version"]} to {pypi_version} outdated libs: {len(outdated_libs)}')
            outdated_libs.append(lib["name"])
        else:
            pass  # print(f'{lib["name"]} is up to date')
    print(f'outdated libs: {len(outdated_libs)} error list: {len(error_list)}')
    return outdated_libs, error_list

def get_args():
    ap = argparse.ArgumentParser(prog="pip_search", description="Search for packages on PyPI")
    ap.add_argument("-s","--sort",type=str, const="name",nargs="?",choices=['name', 'version', 'released', 'stars','watchers','forks'],help="sort results by package name, version or release date (default: %(const)s)")
    ap.add_argument("query", nargs="*", type=str, help="terms to search pypi.org package repository")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--date_format", type=str, default="%d-%m-%Y", nargs="?", help="format for release date, (default: %(default)s)")
    ap.add_argument("-e", "--extra", action="store_true", default=False, help="get extra github info")
    ap.add_argument("-d", "--debug", action="store_true", default=False, help="debugmode")
    ap.add_argument("-l", "--links", action="store_true", default=False, help="show links")
    ap.add_argument("--chklocallibs", action="store_true", default=False, help="check local libs ~/lib/pythonxxx/site-packages ")
    args = ap.parse_args()
    return args
