import sys
from urllib import request
from tabulate import tabulate

def search () :

	f = request.urlopen('https://pypi.org/search/?q=%s' % sys.argv[1])
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
    search()