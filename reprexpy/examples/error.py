import re

# i'm trying to test whether a pattern is contained in a string using the
# re package.
string = 'i love the reprexpy package'
pattern = 'reprexpy'

# the first problem i ran into was a "TypeError":
re.match(pattern)

# turns out i just forgot to provide the `string` argument. however, when i
# do provide the string argument, i'm still not getting a match:
bool(re.match(pattern, string))

# could it maybe be b/c i'm using the wrong function? when i use the `search`
# function i get the output that i expect:
bool(re.search(pattern, string))
