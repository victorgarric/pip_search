import sys
from urllib import request
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

	raw_names=raw_text.split('<span class="package-snippet__name">')[1:-2]
	names=[]
	for name in raw_names :
		names.append(name.split('</span>')[0])


	raw_desc=raw_text.split('<p class="package-snippet__description">')[1:-2]
	descs=[]
	for desc in raw_desc :
		descs.append(desc.split('</p>')[0])

	header=[['Name', 'Description'],['','']]
	rows=[[names[i],descs[i]] for i in range(len(names))]
	print(tabulate(header+rows))

if __name__ == '__main__':
	main()