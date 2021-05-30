import sys
from os import path

from setuptools import setup

install_requires = [
    'pyperclip', 'asttokens', 'nbconvert<=6.0.1', 'nbformat', 'matplotlib', 'ipython',
    'pyimgur', 'setuptools', 'stdlib-list', 'ipykernel', 'tornado'
]

is_v2 = sys.version_info[0] == 2
is_low_v3 = sys.version_info[0] == 3 and sys.version_info[1] <= 4
if is_v2:
    install_requires.remove('ipython')
    install_requires.append('ipython<6')
    install_requires.remove('ipykernel')
    install_requires.append('ipykernel<4.9')

if is_v2 or is_low_v3:
    install_requires.remove('matplotlib')
    install_requires.append('matplotlib<3')

# "Beginning with Matplotlib 3.1, Python 3.6 or above is required", so if we're
# building against python 3.5, we have to require matplotlib < 3.1. otherwise
# we'll get latest version of matplotlib which will throw error
if sys.version_info[0] == 3 and sys.version_info[1] == 5:
    install_requires.remove('matplotlib')
    install_requires.append('matplotlib<3.1')

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

# Only include pytest-runner in setup_requires if we're invoking tests
if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
    setup_requires = ['pytest-runner']
else:
    setup_requires = []
    
setup(
    name='reprexpy',
    version='0.3.0',
    description='Render reproducible examples of Python code (port of R '
                'package `reprex`)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Christopher Baker',
    author_email='chriscrewbaker@gmail.com',
    url='https://reprexpy.readthedocs.io/en/latest',
    license='LICENSE.txt',
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    packages=['reprexpy'],
    install_requires=install_requires,
    tests_require=['pytest', 'pyzmq', 'pickledb'],
    setup_requires=setup_requires,
    package_data={
        'reprexpy': ['examples/*.py'],
    }
)
