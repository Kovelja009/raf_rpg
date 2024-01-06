import gym
import requests
from tactics import Tactics

class RafRpg(gym.Env):
  def __init__(self, input_size, number, agent) -> None:
    super().__init__()
    self.input_size = input_size
    self.url_root = "http://localhost:8082"
    self.prev_value = 0
    self.agent = agent
    url = self.url_root+f"/map/restart?map_number={number}"
    payload={}
    headers = {}
    response = requests.request("PUT", url, headers=headers, data=payload)
    tt = response.json()
    # print(tt,type(tt))
    self.tactics = Tactics(self.url_root, input_size=self.input_size)

    
  def reset(self,number):

    url = self.url_root+f"/map/restart?map_number={number}"
    payload={}
    headers = {}
    response = requests.request("PUT", url, headers=headers, data=payload)
    output = response.json()
    # print(output)
    self.tactics = Tactics(self.url_root, input_size=self.input_size)
    return output

  def step(self,action):
    prev, curr, new_field = self.tactics.step(action)

    if self.agent == 1:
      reward = self.tactics.agent_one_reward(prev, curr, has_moved=self.tactics.has_moved(action), new_field=new_field)
    if self.agent == 2:
      reward = self.tactics.agent_two_reward(prev, curr, has_moved=self.tactics.has_moved(action), new_field=new_field)
    if self.agent == 3:
      reward = self.tactics.agent_three_reward(prev, curr, has_moved=self.tactics.has_moved(action), new_field=new_field)

    is_over = self.tactics.is_over()

    return self.tactics.current_map, reward, is_over, {}
  
  def return_nn_input(self, position, map):
    if self.agent == 1:
      return self.tactics.agent_one_input(position, map)
    if self.agent == 2:
      return self.tactics.agent_two_input(position, map)
    if self.agent == 3:
      return self.tactics.agent_three_input(position, map)

  def render(self):
    payload={}
    headers = {}

    url = self.url_root + "/map/full/matrix"
    response = requests.request("GET", url, headers=headers, data=payload)
    next_observation = response.json()

    return next_observation