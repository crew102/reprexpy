```python
import matplotlib.pyplot as plt

data = [1, 2, 3, 4]

# i'm creating a plot here
plt.plot(data);
plt.ylabel('some numbers');
plt.show()
```

![](https://i.imgur.com/InL6CWO.png)

```python
plt.close()

# another plot
plt.plot(data);
plt.xlabel('more numbers');
plt.show()
```

![](https://i.imgur.com/x60JJsy.png)

```python
plt.close()

# final plot
plt.plot(data);
plt.show()
```

![](https://i.imgur.com/8djqstY.png)
