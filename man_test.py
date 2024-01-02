from openai_gym import RafRpg
import numpy as np

if __name__ == "__main__":
    game = RafRpg()
    observation = game.render()
    print(observation)
    while True:
        key = input()
        if key == 'w':
            up = [1,0,0,0,0]
            observation, reward, is_over, _ = game.step(up)
            print(observation)
            print('------------------------------')
            print('Reward:', reward)
        elif key == 's':
            down = [0,1,0,0,0]
            observation, reward, is_over, _ = game.step(down)
            print(observation)
            print('------------------------------')
            print('Reward:', reward)
        elif key == 'a':
            left = [0,0,1,0,0]
            observation, reward, is_over, _ = game.step(left)
            print(observation)
            print('------------------------------')
            print('Reward:', reward)
        elif key == 'd':
            right = [0,0,0,1,0]
            observation, reward, is_over, _ = game.step(right)
            print(observation)
            print('------------------------------')
            print('Reward:', reward)
        elif key == 'q':
            break
        else:
            print("Invalid input")

        if is_over:
            print("Game over")
            break