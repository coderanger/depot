#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup, find_packages

setup(
    name = 'depot',
    version = '0.0.3',
    packages = find_packages(),
    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    description = 'Manage package repositories in the cloud.',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    license = 'BSD',
    keywords = '',
    url = 'http://github.com/coderanger/depot',
    classifiers = [
        #'Development Status :: 1 - Planning',
        'Development Status :: 2 - Pre-Alpha',
        #'Development Status :: 3 - Alpha',
        #'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    zip_safe = False,
    install_requires = ['apache-libcloud', 'docopt', 'six', 'lockfile', 'arpy', 'python-gnupg'],
    tests_require = ['unittest2', 'mock'],
    test_suite = 'unittest2.collector',
    entry_points = {
        'console_scripts': [
            'depot = depot:main',
        ],
    }
)
