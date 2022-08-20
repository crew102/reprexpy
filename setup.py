import os
import sys

from setuptools import setup

install_requires = [
    'pyperclip', 'asttokens', 'nbconvert', 'nbformat', 'matplotlib',
    'ipython', 'pyimgur', 'stdlib-list', 'ipykernel', 'tornado'
]

# "Beginning with Matplotlib 3.1, Python 3.6 or above is required", so if we're
# building against python 3.5, we have to require matplotlib < 3.1. otherwise
# we'll get latest version of matplotlib which will throw error
is_v35 = sys.version_info[0] == 3 and sys.version_info[1] == 5
if is_v35:
    install_requires.remove('matplotlib')
    install_requires.append('matplotlib<3.1')

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
    setup_requires = ['pytest-runner']
else:
    setup_requires = []

setup(
    name='reprexpy',
    version='0.3.2',
    description='Render reproducible examples of Python code (port of R '
                'package `reprex`)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Christopher Baker',
    author_email='chriscrewbaker@gmail.com',
    url='https://reprexpy.readthedocs.io/en/latest',
    license='LICENSE.txt',
    packages=['reprexpy'],
    install_requires=install_requires,
    tests_require=['pytest', 'pyzmq', 'pickledb'],
    setup_requires=setup_requires,
    python_requires='>=3.5',
    package_data={'reprexpy': ['examples/*.py']}
)
