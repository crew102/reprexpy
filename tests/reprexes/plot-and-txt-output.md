```python
import matplotlib.pyplot as plt


def _plot_and_txt_output_per_statement():
    data = [1, 2, 3, 4]
    plt.plot(data);
    plt.show()

    plt.plot(data);
    plt.show()

    print(data)


_plot_and_txt_output_per_statement()
#> [1, 2, 3, 4]
```

![](https://i.imgur.com/KjGmsCa.png)

![](https://i.imgur.com/CEtVvtC.png)
