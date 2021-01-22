import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pip_search",
    version="0.0.5",
    author="Victor Garric",
    author_email="victor.garric@gmail.com",
    url='https://github.com/victorgarric/pip_search',
    description="A package to search like pip used to via PyPi",
    packages=setuptools.find_packages(),
	install_requires=['tabulate'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.',
	entry_points={
        "console_scripts": [
            "pip_search=pip_search.pip_search:main",
        ],
    },
)
