# Copyright 2018-202x held by ORNL.
# ATS is released under the three-clause BSD License.
# The terms of use and "as is" disclaimer for this license are
# provided in the top-level COPYRIGHT file.
#
# Author: Ethan Coon
#

import os, sys
from os import path
from setuptools import setup, find_packages

min_version = (3, 6)
if sys.version_info < min_version:
    error = """
ats_input_spec does not support Python {0}.{1}.
Python {2}.{3} and above is required. Check your Python version like so:

python3 --version

This may be due to an out-of-date pip. Upgrade pip like so:

pip install --upgrade pip
""".format(*(sys.version_info[:2] + min_version))
    sys.exit(error)

here = path.abspath(path.dirname(__file__))

# read the README
with open(path.join(here, 'README.md'), encoding='utf-8') as readme_file:
    readme = readme_file.read()

# read requirements.txt
with open(path.join(here, 'requirements.txt')) as requirements_file:
    # Parse requirements.txt, ignoring any commented-out lines.
    requirements = [line for line in requirements_file.read().splitlines()
                    if not line.startswith('#')]


setup(
    name='ats_input_spec',
    version='0.1',
    description="Tools for writing and parsing the ATS input spec.",
    long_description=readme,
    author="Ethan Coon",
    author_email="etcoon@gmail.com",
    url="https://github.com/ecoon/ats_input_spec",
    python_requires='>={}'.format('.'.join(str(n) for n in min_version)),
    packages=find_packages(exclude=['tests']),
    install_requires=requirements,
    license="BSD (3-clause)",
)

