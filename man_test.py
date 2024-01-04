from openai_gym import RafRpg
import numpy as np
from model import DeepQNet
import torch as torch

if __name__ == "__main__":
    game = RafRpg()
    observation = game.render()
    inputn = game.tactics.other_input(game.tactics.current_position, observation)
    model = DeepQNet(len(inputn), 5)

    print('------------------------------')
    while True:
        observation = game.tactics.current_map
        # print(observation)
        print('####')
        print(f"Real amount of gold is {game.tactics.current_gold}")
        print('####')
        nn = game.tactics.other_input(game.tactics.current_position, observation)
        print(np.matrix(nn))
        model(torch.tensor(nn, dtype=torch.float))
        key = input()
        if key == 'w':
            up = [1,0,0,0,0]
            observation, reward, is_over, _ = game.step(up)
            # print(observation)
            print('------------------------------')
            print('Reward:', reward)
        elif key == 's':
            down = [0,1,0,0,0]
            observation, reward, is_over, _ = game.step(down)
            # print(observation)
            print('------------------------------')
            print('Reward:', reward)
        elif key == 'a':
            left = [0,0,1,0,0]
            observation, reward, is_over, _ = game.step(left)
            # print(observation)
            print('------------------------------')
            print('Reward:', reward)
        elif key == 'd':
            right = [0,0,0,1,0]
            observation, reward, is_over, _ = game.step(right)
            # print(observation)
            print('------------------------------')
            print('Reward:', reward)
        elif key == 'q':
            break
        else:
            print("Invalid input")


        if is_over:
            print("Game over")
            break