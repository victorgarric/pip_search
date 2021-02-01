import sys
from urllib import request
from bs4 import BeautifulSoup
from tabulate import tabulate

def usage():
	print("Usage:\n  pip_search <keywords>")

def main():
	if (
		len(sys.argv) < 2 or "-h" in sys.argv
		or "--help" in sys.argv or "--usage" in sys.argv
	):
		usage()
	else:
		search()

def search () :
	keyword = ' '.join(sys.argv[1::]).replace(' ', '+')

	f = request.urlopen('https://pypi.org/search/?q=%s' % keyword)
	raw_text=str(f.read())

	soup = BeautifulSoup(raw_text, 'html.parser')
 
	rows = [
		['Name', 'Description'],
		['', '']
	]

	for package in soup.find_all('a', 'package-snippet'):
		name = package.find('span', 'package-snippet__name').text
		description = package.find('p', 'package-snippet__description').text
		rows.append([name, description])

	print(tabulate(rows))

if __name__ == '__main__':
	main()
