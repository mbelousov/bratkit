from setuptools import setup, find_packages
import os

def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''

setup(
    name='bratkit',
    version=__import__('bratkit').__version__,
    author='Maksim Belousov',
    author_email='belousov.maks@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    url='',
    license='',
    description=u' '.join(__import__('bratkit').__doc__.splitlines(
    )).strip(),
    install_requires=[],
    classifiers=[
    ],
    long_description=read_file('README.md'),
)
