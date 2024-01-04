import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import datetime
import os

class DeepQNet(nn.Module):
    def __init__(self, input_size, output_size):
        super(DeepQNet, self).__init__()
        # self.hidden1 = nn.Linear(input_size,192)
        # self.hidden2 = nn.Linear(192, 128)
        # self.output = nn.Linear(128, output_size)

        # first convolutional iteration
        self.input_size = input_size
        self.n_kernels = 32
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=self.n_kernels, kernel_size=(input_size, input_size), padding=0)
        self.hidden1 = nn.Linear(self.n_kernels*1, 192)
        self.hidden2 = nn.Linear(192, 128)
        self.output = nn.Linear(128, output_size)

        # second convolutional iteration
        # 5x5 -> 3x3
        # self.n_kernels = 32
        # self.n_kernels2 = 16
        # self.conv1 = nn.Conv2d(in_channels=1, out_channels=self.n_kernels, kernel_size=(3, 3), padding=0)
        # self.conv2 = nn.Conv2d(in_channels=self.n_kernels, out_channels=self.n_kernels2, kernel_size=(3, 3), padding=0)
        # self.hidden1 = nn.Linear(self.n_kernels2, 192)
        # self.hidden2 = nn.Linear(192, 128)
        # self.output = nn.Linear(128, output_size)


    def forward(self, x):
        # x = F.relu(self.hidden1(x))
        # x = F.relu(self.hidden2(x))
        # x = self.output(x)
        # return x

        # first convolutional iteration
        x = self.conv1(x)
        x = x.view(-1, self.n_kernels*1)
        x = F.relu(self.hidden1(x))
        x = F.relu(self.hidden2(x))
        x = self.output(x)
        
        # second convolutional iteration
        # x = self.conv1(x)
        # x = self.conv2(x)
        # x = x.view(-1, self.n_kernels2)
        # x = F.relu(self.hidden1(x))
        # x = F.relu(self.hidden2(x))
        # x = self.output(x)
        
        return x

    def save(self, file_name='model.pth'):
        model_folder_path = './models'
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)
        # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # timestamped_file_name = f"{os.path.splitext(file_name)[0]}_{timestamp}.pth"
        file_path = os.path.join(model_folder_path, file_name)
        print(f"Saving model to {file_path}")
        torch.save(self.state_dict(), file_path)


class DQNTrainer:
    def __init__(self, model, lr, gamma):
        self.lr = lr #tune lr
        self.gamma = gamma # tune gamma [0.9, 0.99]
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr)
        self.criterion = nn.MSELoss() # tune delta
        self.cum_loss = []

    # reward = immediate reward after performing the action
    # next_state = state after action is performed
    # all values can be either single value or batch of values
    def train_step(self, state, action, reward, next_state, done):
        state = torch.tensor(state, dtype=torch.float)
        next_state = torch.tensor(next_state, dtype=torch.float)
        action = torch.tensor(action, dtype=torch.long)
        reward = torch.tensor(reward, dtype=torch.float)

        # for matrix is 3 (channels, width, height), for nn is 1
        if len(state.shape) == 3:
            state = torch.unsqueeze(state, 0)
            next_state = torch.unsqueeze(next_state, 0)
            action = torch.unsqueeze(action, 0)
            reward = torch.unsqueeze(reward, 0)
            done = (done, )

        # predicted_q_values = self.model(state)

        # target_q_values = predicted_q_values.clone()
        # for idx in range(len(done)):
        #     updated_q_value = reward[idx]

        #     if not done[idx]:
        #         future_q_values = self.model(next_state[idx])
        #         max_future_q = torch.max(future_q_values) # or use mean, because environment is nondeterministic
        #         discounted_max_future_q = self.gamma * max_future_q
        #         updated_q_value = reward[idx] + discounted_max_future_q

        #     action_taken_index = torch.argmax(action[idx]).item()
        #     target_q_values[idx][action_taken_index] = updated_q_value
    
        # self.optimizer.zero_grad()
        # self.criterion(target_q_values , predicted_q_values).backward()
        # self.optimizer.step()
            
            # 1: predicted Q values with current state
        pred = self.model(state)

        target = pred.clone()
        for idx in range(len(done)):
            Q_new = reward[idx]
            if not done[idx]:
                Q_new = reward[idx] + self.gamma * torch.mean(self.model(next_state[idx])) # promenjeno sa max u mean

            target[idx][torch.argmax(action[idx]).item()] = Q_new
    
        # 2: Q_new = r + y * max(next_predicted Q value) -> only do this if not done
        # pred.clone()
        # preds[argmax(action)] = Q_new
        self.optimizer.zero_grad()
        loss = self.criterion(target, pred)
        loss.backward()
        self.cum_loss.append(loss.detach().item())


        self.optimizer.step()



