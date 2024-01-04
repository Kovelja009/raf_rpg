from model import DeepQNet, DQNTrainer
from openai_gym import RafRpg
import torch
import time
import random


if __name__ == "__main__":
    map_number = 1
    epochs = 100
    input_size = 3
    batch_size = 1
    epsilon = 0.0

    game = RafRpg(input_size, map_number)
    input = game.tactics.other_input(game.tactics.current_position, game.tactics.current_map)

    # load torch model
    model = DeepQNet(len(input), 5)
    model.load_state_dict(torch.load('./models/rl1_model.pth'))
    model.eval()

    while not game.tactics.over:

            input = game.tactics.other_input(game.tactics.current_position, game.tactics.current_map)
            
            action = model(torch.tensor(input, dtype=torch.float).unsqueeze(0))
            action_idx = torch.argmax(action).item()
            action = game.tactics.convert_idx_to_action(action_idx)
            map, reward, done, _ = game.step(action)

    print(f"Game over! Gold collected: {game.tactics.current_gold}")            
