# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


#with open('README.rst') as f:
    #readme = f.read()

#with open('LICENSE') as f:
#    license = f.read()

setup(
    name='libmailcd',
    version='0.1.0',
    description='Python Lib Mail CD',
#    long_description=readme,
    author='Matthew Dalrymple',
    author_email='',
    url='',
#    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'pyyaml',
        'click',
        'docker'
        'pygit2',
        'yapsy',
        'keyring',
        'cryptography'
    ],
    #scripts=['bin/mailcd.py']
    entry_points={
        'console_scripts': [
            'mb = libmailcd.cli.main:main',
            'mbs = libmailcd.cli.store:main_store',
            'mbb = libmailcd.cli.build:main_build'
        ]
    }
)
