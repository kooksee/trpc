# -*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='trpc',
    version="0.0.1",
    description='tornado rpc',
    keywords='tornado rpc msgpack',
    author='kooksee',
    author_email='kooksee@163.com',
    url='https://github.com/augustand/trpc',
    license='MIT',
    packages=find_packages('trpc'),
    include_package_data=True,
    zip_safe=True,
)
