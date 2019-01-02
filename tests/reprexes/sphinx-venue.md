    >>> import matplotlib.pyplot as plt
    >>> x = "hi there\nold friend"
    >>> x
    'hi there\nold friend'
    >>> print(x)
    hi there
    old friend
    >>> data = [1, 2, 3, 4]
    >>> # i'm creating a plot here
    >>> plt.plot(data);
    >>> plt.ylabel('some numbers');
    >>> plt.show()

    .. image:: https://i.imgur.com/TRv5sNK.png

    >>> plt.close()