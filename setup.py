# -*- encoding: utf-8 -*-
import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-easy-audit',
    version='1.2rc1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "beautifulsoup4",
    ],
    license='GPL3',
    description='Yet another Django audit log app, hopefully the simplest one.',
    long_description=README,
    url='https://github.com/soynatan/django-easy-audit',
    author='Natán Calzolari',
    author_email='natancalzolari@gmail.com',
    classifiers=[
        'Environment :: Plugins',
        'Framework :: Django',
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
