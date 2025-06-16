import pathlib

from setuptools import find_packages, setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name="pip_search",
    version="0.0.14",
    author="Victor Garric",
    author_email="victor.garric@gmail.com",
    url="https://github.com/victorgarric/pip_search",
    description="A package to search like pip used to, via PyPi",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests",)),
    install_requires=["bs4", "requests", "rich"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.2",
    entry_points={
        "console_scripts": [
            "pip_search=pip_search.__main__:main",
        ],
    },
)
