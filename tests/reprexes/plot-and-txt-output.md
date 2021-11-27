```python
import matplotlib.pyplot as plt


def _plot_and_txt_output_per_statement():
    data = [1, 2, 3, 4]
    plt.plot(data);
    plt.show()
    plt.close()

    plt.plot([3, 3]);
    plt.show()

    print(data)


_plot_and_txt_output_per_statement()
#> [1, 2, 3, 4]
```

![](https://i.imgur.com/faWeRcg.png)

![](https://i.imgur.com/Q6SCLsU.png)
