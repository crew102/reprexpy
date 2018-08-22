import sys
from os import path

from setuptools import setup

install_requires = [
    'pyperclip', 'asttokens', 'nbconvert', 'nbformat', 'matplotlib', 'ipython',
    'pyimgur', 'setuptools', 'stdlib-list', 'jupyter'
]
if sys.version_info[0] == 2:
    install_requires.remove('ipython')
    install_requires.append('ipython<6')

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

setup(
    name='reprexpy',
    version='0.1.0.9000',
    description='Render reproducible examples of Python code (port of R '
                'package `reprex`)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Christopher Baker',
    author_email='chriscrewbaker@gmail.com',
    url='https://github.com/crew102/reprexpy/issues',
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
    setup_requires=["pytest-runner"],
    package_data={
        'reprexpy': ['examples/*.py'],
    }
)
