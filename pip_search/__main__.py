import sys
import argparse
from pip_search.pip_search import search


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('query', nargs='+', type=str,
                    help='terms to search pypi.org package repository')
    args = ap.parse_args()
    search(query=' '.join(args.query))


if __name__ == '__main__':
    sys.exit(main())
