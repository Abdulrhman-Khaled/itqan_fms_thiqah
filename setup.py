from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in itqan_fms/__init__.py
from itqan_fms import __version__ as version

setup(
	name="itqan_fms",
	version=version,
	description="Facility Management",
	author="ITQAN",
	author_email="info@itqan-kw.net",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
