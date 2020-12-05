from os.path import isfile
from setuptools import setup, find_packages

setup(
    name = "circuit_samples",
    version = "0.1.0",
    author = "Simon Wood",
    author_email = "simon@mungewell.org",
    description = "Library for Sample SysEx files for Novation Circuit",
    license = "GPLv3",
    keywords = "Novation Circuit Sample SysEx",
    url = "https://github.com/mungewell/circuit_samples",
    py_modules=["circuit_samples"],
    long_description=open("README.rst").read() if isfile("README.rst") else "",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3"
    ],
)
