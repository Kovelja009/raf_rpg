import matplotlib.pyplot as plt

def plot_training(history):
    # Plot metric over epochs
    plt.plot(history)

    # Add title and axis names
    plt.title('Steps over epochs')
    plt.xlabel('Epoch')
    plt.ylabel('Steps')

if __name__ == "__main__":
    history = []
    with open("logs.txt", "r") as f:
        for line in f:
            history.append(int(line.split(",")[0]))
    plot_training(history)
    plt.show()
