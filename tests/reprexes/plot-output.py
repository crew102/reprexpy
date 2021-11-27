import matplotlib.pyplot as plt

data = [1, 2, 3, 4]

# i'm creating a plot here
plt.plot(data);
plt.ylabel('some numbers');
plt.show()
plt.close()

# another plot
plt.plot([3, 3]);
plt.xlabel('more numbers');
plt.show()
plt.close()

# final plot
plt.plot(data);
plt.show()
