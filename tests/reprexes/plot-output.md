```python
import matplotlib.pyplot as plt

data = [1, 2, 3, 4]

# i'm creating a plot here
plt.plot(data);
plt.ylabel('some numbers');
plt.show()
```

![](https://i.imgur.com/9oW9Zsy.png)

```python
plt.close()

# another plot
plt.plot([3, 3]);
plt.xlabel('more numbers');
plt.show()
```

![](https://i.imgur.com/L4HNklT.png)

```python
plt.close()

# final plot
plt.plot(data);
plt.show()
```

![](https://i.imgur.com/1MedfL6.png)
