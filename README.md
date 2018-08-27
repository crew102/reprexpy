# reprexpy

> Render **repr**oducible **ex**amples of Python code for posting to GitHub/Stack Overflow (port of R package `reprex`)

[![Linux Build Status](https://travis-ci.org/crew102/reprexpy.svg?branch=master)](https://travis-ci.org/crew102/reprexpy)
[![PyPI version](https://img.shields.io/pypi/v/reprexpy.svg)](https://pypi.org/project/reprexpy/)
[![Python versions](https://img.shields.io/pypi/pyversions/reprexpy.svg)](https://pypi.org/project/reprexpy/)

`reprexpy` is a Python package that makes it easy to create **repr**oducible **ex**amples (also known as [reprexes](https://twitter.com/romain_francois/status/530011023743655936) or [minimal working examples (MWEs)](https://en.wikipedia.org/wiki/Minimal_Working_Example)) that are ready to be posted to GitHub or Stack Overflow. It is a port of the R package [reprex](https://github.com/tidyverse/reprex).

## Installation

You can get the stable version from PyPI:

```
pip install reprexpy
```

Or the development version from GitHub:

```
pip install git+https://github.com/crew102/reprexpy.git
```

## A basic example

Let's say you want to know if there's a shortcut for flatting lists in Python, so you create the following MWE to post to SO (example inspired by [this SO question](https://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python)):

```python
# i know that you can flatten a list in python using list comprehension:
l = [[1, 2, 3], [4, 5, 6], [7], [8, 9]]
[item for sublist in l for item in sublist]

# but i'd like to know if there's another way. i tried this but i got an error:
import functools
functools.reduce(lambda x, y: x.extend(y), l)
```

You'd like to put the results of running the above code in the example as well, to show people what you are seeing in your terminal:

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

You could run the code in your terminal and copy/paste the outputs into your example. That can be a pain, though, especially if you have a lot of outputs to copy. An easier way is to use `reprex()`:

![](https://raw.githubusercontent.com/crew102/reprexpy/master/docs/source/gifs/basic-example.gif)

When you run `reprex()`, your code is run inside an IPython kernel and the outputs (including errors) are captured and displayed alongside the code. Details on the IPython session are given as well in a section called "Session Info" (more on this later).

## Including `matplotlib` plots

`reprex()` makes it easy to include `matplotlib` plots in your MWEs. It does this by uploading the plots to imgur and including inline links to them in your example. For example, let's say you have the following example that you want to post to GitHub:

```python
import matplotlib.pyplot as plt

data = [1, 2, 3, 4]

# i'm creating a plot here
plt.plot(data);
plt.ylabel('some numbers');
plt.show()
plt.close()

# another plot
plt.plot(data);
plt.xlabel('more numbers');
plt.show()
plt.close()
```

You can render this reprex (i.e., ready it for posting to GitHub) using `reprex()`:

![](https://raw.githubusercontent.com/crew102/reprexpy/master/docs/source/gifs/plotting.gif)

## `SessionInfo()`

You may have noticed in the previous two examples that a section called "Session Info" is added to the end of your reprex by default. This section includes details about the IPython kernel that was used to render your reprex, such as the Python version that was used and the platform the code was run on. It also includes the version numbers of the packages used in your example (e.g., `matplotlib`). You can use the `SessionInfo()` function to get this information whenever you are using an IPython kernel (e.g., when you are inside an IPython terminal or Jupyter notebook):

```python
import pandas
import requests
import numpy

from reprexpy import SessionInfo
SessionInfo()
#> Session info --------------------------------------------------------------------
#> Date: 2018-08-27
#> Darwin-17.7.0-x86_64-i386-64bit (64-bit)
#> Python: 3.5
#> Packages ------------------------------------------------------------------------
#> numpy==1.15.0
#> pandas==0.23.4
#> reprexpy==0.1.0
#> requests==2.19.1
```
