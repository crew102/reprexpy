# i know you can flatten a list in python using list comprehension:
l = [[1, 2, 3], [4, 5, 6], [7], [8, 9]]
[item for sublist in l for item in sublist]

# but i'd like to know if there's another way. i tried this but i got an error:
import functools
functools.reduce(lambda x, y: x.extend(y), l)
