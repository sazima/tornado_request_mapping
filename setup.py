#!/usr/bin/env python
# coding: utf-8
from setuptools import setup

with open("readme.md", "r", encoding="utf8") as f:
    readme = f.read()

setup(
    name='tornado-request-mapping',
    version='0.0.2',
    author='wukt',
    author_email='w@wktadmin.com',
    url='https://github.com/sazima/tornado-request-mapping',
    description='spring-like request_mapping for tornado.',
    packages=['tornado_request_mapping'],
    long_description=readme,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ], install_requires=['tornado']
)
