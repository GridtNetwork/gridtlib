#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = [
    "passlib",
    "pyjwt",
    "python-http-client",
    "sendgrid",
    "sqlalchemy",
    "starkbank-ecdsa",
]

setup(
    author="Robin A. Dorstijn",
    author_email='info@gridt.org',
    python_requires='>=3.5',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Library for interacting with the Gridt Network database.",
    install_requires=requirements,
    license="MIT license",
    include_package_data=True,
    keywords='gridtlib',
    name='gridtlib',
    packages=find_packages(include=['gridt', 'gridt.*']),
    url='https://github.com/GridtNetwork/gridtlib',
    version='0.0.1',
    zip_safe=False,
)
