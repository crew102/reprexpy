# reprexpy

> Render **repr**oducible **ex**amples of Python code for posting to GitHub/StackOverflow (port of R package `reprex`)

[![Linux Build Status](https://travis-ci.org/crew102/reprexpy.svg?branch=master)](https://travis-ci.org/crew102/reprexpy)
[![PyPI version](https://img.shields.io/pypi/v/reprexpy.svg)](https://pypi.org/project/reprexpy/)
[![Python versions](https://img.shields.io/pypi/pyversions/reprexpy.svg)](https://pypi.org/project/reprexpy/)

`reprexpy` is a Python package that makes it easy to create **repr**oducible **ex**amples (also known as [mimimal working examples (MWE)](https://en.wikipedia.org/wiki/Minimal_Working_Example) or [reprexes](https://twitter.com/romain_francois/status/530011023743655936)) that are ready to be posted to GitHub or Stack Overflow. It is a port of the r package [reprex](https://github.com/tidyverse/reprex).

## Installation

You can get the stable version from PyPI:

```
pip install reprexpy
```

Or the development version from GitHub:

```
pip install git+https://github.com/crew102/reprexpy.git
```

## Motivation

Let's say you want to know if there's a shortcut for flatting lists in Python. You create the following MWE to post to SO (example inspired by [this SO question](https://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python))

```python
# i know that you can flatten a list in python using list comprehension:
l = [[1, 2, 3], [4, 5, 6], [7], [8, 9]]
[item for sublist in l for item in sublist]

# but i'd like to know if there's another way. i tried this but i got an error:
import functools
functools.reduce(lambda x, y: x.extend(y), l)
```

You'd like to put the results of running this code in the example as well, to show people what you are seeing in your terminal:

```python
# i know that you can flatten a list in python using list comprehension:
l = [[1, 2, 3], [4, 5, 6], [7], [8, 9]]
[item for sublist in l for item in sublist]
#> [1, 2, 3, 4, 5, 6, 7, 8, 9]

# but i'd like to know if there's another way. i tried this but i got an error:
import functools
functools.reduce(lambda x, y: x.extend(y), l)
#> Traceback (most recent call last):
#>  File "<stdin>", line 1, in <module>
#>  File "<stdin>", line 1, in <lambda>
#> AttributeError: 'NoneType' object has no attribute 'extend'
```

You run the code in your terminal, copy and pasting the outputs into your example. That can be a pain, though, especially if you have a lot of outputs to copy over. An easier way to include the results of your example into the example itself is to use `reprex()`:

## `SessionInfo()`

