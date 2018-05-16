from setuptools import setup
from codecs import open
from os import path

# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='reprexpy',
    version='0.1.0.devl',
    description='Render reproducible examples of code (port of R package `reprex`)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Christopher Baker',
    author_email='chriscrewbaker@gmail.com',
    url='https://github.com/crew102/reprexpy/issues',
    classifiers=[
    ],
    packages='reprexpy',
    install_requires=[
        'pyperclip'
    ]
)