import sys
import argparse
from pip_search.pip_search import search


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--sort", action="store_true",
                    help="sort results by package name")
    ap.add_argument('query', nargs='+', type=str,
                    help='terms to search pypi.org package repository')
    args = ap.parse_args()
    search(query=' '.join(args.query), opts=args)


if __name__ == '__main__':
    sys.exit(main())
