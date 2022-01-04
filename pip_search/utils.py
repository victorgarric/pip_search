from sys import version_info as py_ver

if py_ver[0] == 3 and py_ver[1] >= 8:

	from importlib.metadata import PackageNotFoundError
	from importlib.metadata import version as pkg_version


	def check_version(package: str):
		try:
			return pkg_version(package)
		except PackageNotFoundError:
			return False

else:
	import pkg_resources as pkg
	def check_version(package: str):
		try:
			return pkg.get_distribution(package).version
		except :
			return False
