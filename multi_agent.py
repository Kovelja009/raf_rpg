from model import DeepQNet
from tactics import Tactics
import torch
import requests
import random

class MultiAgent:
    def __init__(self, map_number, max_moves, path_agent1='./models/rl1_model.pth', path_agent2='./models/rl2_model.pth'):
        self.url_root = "http://localhost:8082"
        self.agent1 = DeepQNet(3, 5)
        self.agent2 = DeepQNet(3, 5)
        self.agent1.load_state_dict(torch.load(path_agent1))
        self.agent2.load_state_dict(torch.load(path_agent2))
        self.agent1.eval()
        self.agent2.eval()
        self.tactics = Tactics(self.url_root, input_size=3)
        self.map_number = map_number
        url = self.url_root+f"/map/restart?map_number={map_number}"
        requests.request("PUT", url, headers={}, data={})
        self.modes = [1, 2, 3]
        self.current_mode = 1
        self.max_moves = max_moves
        self.current_moves = 0
        self.previous_pos, _ = self.tactics.get_player_position()
        self.same_pos_cnt = 0

    def reset(self, map_number):
        url = self.url_root+f"/map/restart?map_number={map_number}"
        requests.request("PUT", url, headers={}, data={})
        self.tactics = Tactics(self.url_root, input_size=3)

    def do_action(self):
        map = self.tactics.get_map()
        position, _ = self.tactics.get_player_position()
        self.tactics.update_gold_amount()
        self.tactics.update_inventory()

        # somehow gets stuck
        if self.same_pos_cnt > 10:
            self.same_pos_cnt = 9
            action_idx = random.randint(0, 4)
            action = self.tactics.convert_idx_to_action(action_idx)
        else:
            # go to the gate
            if self.tactics.current_gold >= 53:
                self.current_mode = 3
            # go to the merchant
            elif self.tactics.get_inventory_value() + self.tactics.current_gold >= 53:
                self.current_mode = 2
            # collect items
            else:
                self.current_mode = 1

            if self.current_mode == 1:
                input = self.tactics.agent_one_input(position, map)
                action = self.agent1(torch.tensor(input, dtype=torch.float).unsqueeze(0))

            elif self.current_mode == 2:
                input = self.tactics.agent_two_input(position, map)
                action = self.agent2(torch.tensor(input, dtype=torch.float).unsqueeze(0))
            else:
                input = self.tactics.agent_three_input(position, map)
                action = self.agent2(torch.tensor(input, dtype=torch.float).unsqueeze(0))

            action_idx = torch.argmax(action).item()
            action = self.tactics.convert_idx_to_action(action_idx)
        self.tactics.step(action)
        self.current_moves += 1

        new_pos, _ = self.tactics.get_player_position()

        if new_pos == self.previous_pos:
            self.same_pos_cnt += 1
        else:
            self.same_pos_cnt = 0
        self.previous_pos = new_pos

    def is_over(self):
        url = self.url_root + "/map/isover"
        response = requests.request("GET", url, headers={}, data={})
        done = response.json()
        return done or self.current_moves >= self.max_moves
