import matplotlib.pyplot as plt

def plot_training(history, history2):
    # plot 2 metrics on the same figure, side by side
    plt.subplot(1, 2, 1)
    plt.plot(history)
    plt.title('Steps over epochs')
    plt.xlabel('Epoch')
    plt.ylabel('Steps')

    plt.subplot(1, 2, 2)
    plt.plot(history2, color='purple')
    plt.title('Loss over epochs')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    
if __name__ == "__main__":
    history = []
    with open("logs_step2.txt", "r") as f:
        for line in f:
            history.append(int(line.split(",")[0]))

    history2 = []
    with open("logs_loss2.txt", "r") as f:
        for line in f:
            history2.append(float(line.split(",")[0]))
    plot_training(history, history2)
    plt.show()
