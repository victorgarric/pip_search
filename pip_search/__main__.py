import sys
import requests
from pip_search.pip_search import search


import subprocess
import sys
import re
import pickle
from pathlib import Path

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter, ThreadedCompleter


# Could be maybe used for installation of the packages
# def install_package(package):
#     subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def refresh_packages_list():
    page = requests.get("https://pypi.org/simple/")
    data = page.text
    filtered = re.findall(r">(.*)</a>", data)

    with open("package_list", "wb") as f:
        pickle.dump(filtered, f)

def load_packages_list():

    file = Path("package_list")

    if(not file.is_file()):
        refresh_packages_list()


    with open("package_list", "rb") as f:
        filtered = pickle.load(f)
    return filtered

def main():
    package_list = load_packages_list()
    query = (prompt(">", completer = ThreadedCompleter(WordCompleter(package_list, sentence=True, pattern=re.compile(r'(.*)')))))
    search(query=query)


if __name__ == '__main__':
    sys.exit(main())
