import sys
from setuptools import setup, find_packages


if sys.version_info < (3, 7):
    raise RuntimeError('aiodag requires Python 3.7+')


classifiers = [
    'License :: OSI Approved :: MIT License',
    'Intended Audience :: Developers',
    'Programming Language :: Python :: 3',
    'Framework :: AsyncIO',
]


keywords = ["dag", "asyncio", "aiodag"]


setup(
    name='aiodag',
    version='0.3',
    description=('Build and execute AsyncIO powered DAGs.'),
    classifiers=classifiers,
    platforms=['POSIX'],
    author="aa1371",
    url='https://github.com/aa1371/aiodag',
    download_url='https://github.com/aa1371/aiodag/archive/refs/tags/v0.3.tar.gz',
    license='MIT',
    packages=find_packages(exclude=['tests', 'tests.*']),
    keywords=keywords
)
