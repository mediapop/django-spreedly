#!/usr/bin/env python
"""
=============================================================================
django-spreedly
=============================================================================

This app can be used to add support for the spreedly subscription service to your django app.
"""

from setuptools import setup, find_packages


install_requires = [
    'path.py',
    'django<1.5',
    'pytz',
    'pyspreedly',
]

tests_requires = [
    'mock',
    'south'
]

setup(
    name='django-spreedly',
    version='2.0.9',
    author='James Rivett-Carnac',
    author_email='dev@mediapop.co',
    url='www.github.com/mediapop/django-spreedly',
    description='django-spreedly integrates support for the spreedly '
                'subscription service',
    long_description=__doc__,
    packages=find_packages(exclude=("tests",)),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'tests': tests_requires
    },
    test_suite='tests.run_tasks.run_tests',
    include_package_data=True,
    entry_points={},
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Django'
    ],
)
