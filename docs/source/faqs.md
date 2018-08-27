## FAQs

**1. How do I suppress the output the intermediate matplotlib functions in my reprex?**

Just add a `;` to the relevant function call. For example, you can suppress `[<matplotlib.lines.Line2D at 0x187f37b8>]` below:
  
```python
import matplotlib.pyplot as plt
data = [1, 2, 3, 4]

# If you don't want to see the output of this function:
plt.plot(data)
#> [<matplotlib.lines.Line2D at 0x187f37b8>] 

# ...just add a ";"
plt.plot(data);
```

**2. Why can't I use SessionInfo() inside a script that I run, or inside a regular terminal?**

`SessionInfo()` requires IPython to be running in order for it to gather information about the current session.

**3. How do I print pandas data frames in reprexes?**

You may have noticed that a data frame's `__repr__` method doesn't play well with reprex:
  
```python
import pandas as pd
d = {'col1': [1, 2], 'col2': [3, 4]}
df = pd.DataFrame(data=d)
df
#>    col1  col2
0     1     3
1     2     4
```

See how only the first line of output is commented out above? To comment out each line of output, you have to explicitly call `print()`:
  
```python
print(df)
#>    col1  col2
#> 0     1     3
#> 1     2     4
```

**4. reprex() can't seem to access my clipboard on Linux. What can I do?**

You may need to install `xclip` or `xsel`. If you're using the Debian packaging system, you can try:

```bash
sudo apt-get install xclip
sudo apt-get install xsel
```
