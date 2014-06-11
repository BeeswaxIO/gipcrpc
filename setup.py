# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(
    name='gipcrpc',
    version='0.0.1',
    description='RPC framework for parent and children using gipc(gevent)',
    long_description=open('README.rst').read(),
    author='Studio Ousia',
    author_email='admin@ousia.jp',
    url='http://github.com/studio-ousia/gipcrpc',
    packages=find_packages(),
    license=open('LICENSE').read(),
    include_package_data=True,
    keywords=['gevent', 'ipc', 'rpc'],
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ),
    install_requires=[
        'Cython',
        'gevent',
        'gipc',
    ],
    tests_require=[
        'nose',
        'mock',
    ],
    test_suite = 'nose.collector'
)