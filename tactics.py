import requests
import time
import numpy as np
from collections import deque

# diamond -> 20
# gem -> 14
# apple -> 7
# rice -> 4
# stone -> 3
# wood, bones -> 2
# grass -> 0

#########################
# Lawn (discovered: '.', undiscovered: '_'): Diamond(20), Grass(0), Rice (4)
# Forest (discovered: ':', undiscovered: '+'): Stone(3), Apple(7), Wood(2)
# Highland (discovered: '<', undiscovered: '>'): Bones(2), Diamond(20), Grass(0), Wood(2) 
# Water ('-')
# Gate ('|')
# Mountain ('$')

#########################
# Player ('P')
# Villager ('V'): Diamond(20), Rice(4), Wood(2)
# Bandit ('B')
# Merchant ('M')

class Tactics():
    def __init__(self, url_root, max_moves=128, max_gold=55, input_size=3, villager_rate=150, merchant_rate=0.2, bandit_rwd=-1000, discovered_penalty=-800, invalid_penalty=-1000, waiting_penalty=-1000, insufficient_moves= -100, lawn_rwd=['Diamond', 'Grass', 'Rice'], forest_rwd=['Stone', 'Apple', 'Wood'], highland_rwd=['Bones', 'Diamond', 'Grass', 'Wood'], villager_rwd=['Diamond', 'Rice', 'Wood']):
        self.max_moves = max_moves
        self.url_root = url_root
        self.max_gold = max_gold
        self.merchant_rate = merchant_rate
        self.villager_rate = villager_rate
        self.bandit_rwd = bandit_rwd
        self.discovered_penalty = discovered_penalty
        self.invalid_penalty = invalid_penalty
        self.insufficient_moves = insufficient_moves
        self.waiting_penalty = waiting_penalty


        self.eval_lst = []

        # Values of items
        self.item_values = {'Diamond': 20, 'Gem': 14, 'Apple': 7, 'Rice': 4, 'Stone': 3, 'Wood': 2, 'Bones': 2, 'Grass': 0}

        # Rewards for stepping on a field
        self.lawn_rwd = self.get_field_reward(lawn_rwd)
        self.forest_rwd = self.get_field_reward(forest_rwd)
        self.highland_rwd = self.get_field_reward(highland_rwd)
        self.villager_rwd = self.get_field_reward(villager_rwd)

        # input details
        self.input_size = input_size

        # Agent one
        self.xlost = -5
        self.xwon = 5
        self.xundiscovered = 2
        self.xdiscovered = -2
        self.xunreachable = -4
        self.xplayer = -3
        self.xvillager = 3
        self.xbandit = -4
        self.xmerchant = -2
        self.xgate = -2
        self.xout_of_bounds = -5

        # Agent two

        self.xxlost = -4
        self.xxwon = 10
        self.xxundiscovered = 0
        self.xxdiscovered = 0
        self.xxunreachable = -3
        self.xxplayer = -3
        self.xxvillager = -2
        self.xxbandit = -5
        self.xxmerchant = 10
        self.xxgate = 0
        self.xxout_of_bounds = -4

        self.inv_dist = 100
        self.pseudo_cnt = 0

        # Characters
        self.player = 'P'
        self.villager = 'V'
        self.bandit = 'B'
        self.merchant = 'M'

        # Fields
        self.lawn = '_'
        self.forest = '+'
        self.highland = '>'
        self.water = '-'
        self.gate = '|'
        self.mountain = '$'
        self.discovered = ['.', ':', '<']
        self.undiscovered = ['_', '+', '>']
        self.unreachable = [self.water, self.mountain]

        self.current_inventory = None
        self.update_inventory()
        self.current_gold = 0
        self.update_gold_amount()
        self.current_position = self.get_player_position()
        self.current_moves = 0
        self.over = False
        self.current_map = self.get_map()

        # for bfs rl_agent2
        self.bfs_not_allowed2 = [self.water, self.mountain, self.villager, self.bandit]
        
        # for bfs rl_agent3
        self.bfs_not_allowed3 = [self.water, self.mountain, self.villager, self.bandit, self.merchant]
        

    def get_field_reward(self, field_rwd):
        reward = 0
        for rwd in field_rwd:
            reward += self.item_values[rwd]
        
        return reward/len(field_rwd)
    

    def get_player_position(self, action=None):
        map = self.get_map()

        for i, row in enumerate(map):
            for j, field in enumerate(row):
                if field == self.player:
                    if action in [[1,0,0,0,0], [0,1,0,0,0], [0,0,1,0,0], [0,0,0,1,0]]:
                        return (i, j), map[i-action[0]+action[1]][j+action[3]-action[2]]
                    else:
                        return (i, j), self.player
        print('Error: There is no player on the map!')
        return None
    
    def get_map(self):
        url = self.url_root + "/map/full/matrix"
        response = requests.request("GET", url, headers={}, data={})
        map = response.json()
        return map

    def convert_idx_to_action(self, idx):
        # up
        if idx == 0:
            # print('UP')
            return [1,0,0,0,0]
        # down
        elif idx == 1:
            # print('DOWN')
            return [0,1,0,0,0]
        # left
        elif idx == 2:
            # print('LEFT')
            return [0,0,1,0,0]
        # right
        elif idx == 3:
            # print('RIGHT')
            return [0,0,0,1,0]
        # wait
        elif idx == 4:
            # print('WAIT')
            return [0,0,0,0,1]
        else:
            print(f'Error: Invalid action index: {idx}!')
            return None
    
    def step(self, action):
        prev_position, next_field = self.get_player_position(action)

        url_sufix = "wait"
        if action == [1,0,0,0,0]:
            url_sufix = "up"
        elif action == [0,1,0,0,0]:
            url_sufix = "down"
        elif action == [0,0,1,0,0]:
            url_sufix = "left"
        elif action == [0,0,0,1,0]:
            url_sufix = "right"
        elif action == [0,0,0,0,1]:
            url_sufix = "wait"

        url = self.url_root + "/player/" + url_sufix
        payload={}
        headers = {}
        requests.request("PUT", url, headers=headers, data=payload)
        time.sleep(0.2)

        self.current_moves += 1
        self.current_position, _ = self.get_player_position()
        self.current_map = self.get_map()
        return prev_position, self.current_position, next_field
        
    def has_moved(self, action):
        if action == [0,0,0,0,1]:
            return False
        return True
    

    def is_over(self):
        if self.current_moves >= self.max_moves or self.over:
            return True
        return False

    def get_inventory_value(self):
        cum_value = 0
        for key, value in self.current_inventory.items():
            cum_value += self.item_values[key] * value
        return cum_value
    
    def update_inventory(self):
        url = self.url_root + "/player/inventory"
        response = requests.request("GET", url, headers={}, data={})
        inventory = response.json()

        if inventory == None:
            self.current_inventory = {'Diamond': 0, 'Gem': 0, 'Apple': 0, 'Rice': 0, 'Stone': 0, 'Wood': 0, 'Bones': 0, 'Grass': 0}
        else:
            self.current_inventory = inventory

    def update_gold_amount(self):
        url = self.url_root + "/player/inventory/gold"
        response = requests.request("GET", url, headers={}, data={})
        self.current_gold = response.json()

    def in_bandit_range(self, my_position, map):
        for i, row in enumerate(map):
            for j, field in enumerate(row):
                if field == self.bandit:
                    if abs(i-my_position[0]) + abs(j-my_position[1]) <= 2:
                        return True
        return False
    
    def manhattan_distance(self, my_position, field, map):
        closest_field = None
        closest_distance = 1000
        x = 1000
        y = 1000
        for i, row in enumerate(map):
            for j, f in enumerate(row):
                if f == field:
                    distance = abs(i-my_position[0]) + abs(j-my_position[1])
                    if distance < closest_distance:
                        closest_distance = distance

                        closest_field = (i, j)

        return closest_distance, closest_field
    
    # you can go only on discovered and undiscovered fields
    # also cant go near bandit
    # distance to the field acording to the rules
    def bfs_distance(self, my_position, target_field, map, not_allowed_fields):
        # find target_field
        target_i, target_j = 0, 0
        for i, row in enumerate(map):
            for j, field in enumerate(row):
                if field == target_field:
                    target_i, target_j = i, j
                    break

        rows_n = len(map)
        cols_n = len(map[0])

        # up, down, left, right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        queue = deque([my_position])
        visited = [[False for _ in range(cols_n)] for _ in range(rows_n)]
        visited[my_position[0]][my_position[1]] = True
        distance = 0
        path = {}

        while queue:
            size = len(queue)
            distance += 1
            for _ in range(size):
                curr_i, curr_j = queue.popleft()

                for dir_i, dir_j in directions:
                    new_i = curr_i + dir_i
                    new_j = curr_j + dir_j

                    if new_i < 0 or new_i >= rows_n or new_j < 0 or new_j >= cols_n:
                        continue
                    
                    # if valid unvisited, not near bandit field 
                    if visited[new_i][new_j] == False and map[new_i][new_j] not in not_allowed_fields and not self.near_bandit((new_i, new_j), map, target_field):
                        path[(new_i, new_j)] = (curr_i, curr_j)
                        if new_i == target_i and new_j == target_j:
                            # Reconstruct the shortest path
                            shortest_path = [(new_i, new_j)]
                            while (new_i, new_j) != (my_position[0], my_position[1]):
                                new_i, new_j = path[(new_i, new_j)]
                                shortest_path.append((new_i, new_j))
                            shortest_path.reverse()
                            return distance, shortest_path
                        
                        visited[new_i][new_j] = True
                        queue.append((new_i, new_j))

        return None, None


                

    def near_bandit(self, position, map, target_field):
        if map[position[0]][position[1]] == target_field:
            return False
        
        for i, row in enumerate(map):
            for j, field in enumerate(row):
                if field == self.bandit:
                    # only + fields around bandit
                    if abs(i-position[0]) + abs(j-position[1]) <= 1:
                        return True
        return False


    
    def x_y_manhattan_distance(self, my_position, field, map):
        distance, closest_field = self.manhattan_distance(my_position, field, map)

        if closest_field == None:
            return 100, 100, 100
        # x, y
        return closest_field[1] - my_position[1], closest_field[0] - my_position[0], distance
     
    
    # conv net
    def agent_one_input(self, my_position, map):
        
        # make matrix
        matrix = self.make_matrix(my_position, map)
        return matrix

    def make_matrix(self, my_position, map):
        matrix = []
        for i, row in enumerate(map):
            for j, field in enumerate(row):
                if field == self.player:
                    # 5x5_matrix (initial)
                    row_bound = int(np.floor(self.input_size/2))
                    row_bound1 = int(np.floor(self.input_size/2))
                    row_bound2 = 1

                    for _ in range(self.input_size):
                        if row_bound1 >= 0:
                            matrix.append(self.make_row(i-row_bound1, j, map, len(map), len(map[0]), self.input_size))
                            row_bound1 -= 1                                           
                        else:
                            matrix.append(self.make_row(i+row_bound2, j, map, len(map), len(map[0]), self.input_size))
                            row_bound2 += 1
                        if row_bound2 > row_bound:
                            break
                    return matrix
            
        print('No player on the map -> for input!')
        return None
                    
    def gfw(self, field):
        if field in self.discovered:
            return self.xdiscovered
        elif field in self.undiscovered:
            return self.xundiscovered
        elif field in self.unreachable:
            return self.xunreachable
        elif field == self.player:
            return self.xplayer
        elif field == self.villager:
            return self.xvillager
        elif field == self.bandit:
            return self.xbandit
        elif field == self.merchant:
            return self.xmerchant
        elif field == self.gate:
            return self.xgate
        else:
            return self.xout_of_bounds

    def make_row(self, i, j, map, bound_i, bound_j, n):
        row = []
        # invalid row
        if i < 0 or i >= bound_i:
            for _ in range(n):
                row.append(self.xout_of_bounds)
            return row
        
        col_bound = int(np.floor(n/2))
        
        for k in range(n):
            idx = k - col_bound
            # invalid field
            if j + idx < 0 or j + idx >= bound_j:
                row.append(self.xout_of_bounds)
            # valid field
            else:
                row.append(self.gfw(map[i][j+idx]))
        
        return row
    
    def agent_two_input(self, my_position, map):     
        matrix = self.make_matrix2(my_position, map, self.merchant, self.bfs_not_allowed2)
        return matrix
    
    def agent_three_input(self, my_position, map):
        matrix = self.make_matrix2(my_position, map, self.gate, self.bfs_not_allowed3)
        return matrix

    # 3x3 matrix around player
    def make_matrix2(self, my_position, map, goal_field, not_allowed_fields):
        matrix = [[0,0,0],[0,0,0],[0,0,0]]
        pi, pj = my_position

        dist, path = self.bfs_distance(my_position, goal_field, map, not_allowed_fields)

        if dist == None:
            print('Distance None in BFS!')
            return matrix

        first_step = path[1]

        # if first step is up
        if first_step == (pi - 1, pj):
            matrix[0][1] = self.xxmerchant
        # if first step is down
        elif first_step == (pi + 1, pj):
            matrix[2][1] = self.xxmerchant
        # if first step is left
        elif first_step == (pi, pj - 1):
            matrix[1][0] = self.xxmerchant
        # if first step is right
        elif first_step == (pi, pj + 1):
            matrix[1][2] = self.xxmerchant
        else:
            raise Exception(f'First step not valid: !')

        return matrix



    def gfw2(self, i, j, i_bound, j_bound, map):
        field = map[i][j]
        if i < 0 or i >= i_bound or j < 0 or j >= j_bound:
            return self.xxout_of_bounds
        else:
            if field in self.discovered:
                return self.xxdiscovered
            elif field in self.undiscovered:
                return self.xxundiscovered
            elif field in self.unreachable:
                return self.xxunreachable
            elif field == self.player:
                return self.xxplayer
            elif field == self.villager:
                return self.xxvillager
            elif field == self.bandit:
                return self.xxbandit
            elif field == self.merchant:
                return self.xxmerchant
            elif field == self.gate:
                return self.xxgate
            else:
                return self.xxout_of_bounds

    # Agent 1 
    def agent_one_reward(self, old_position, new_position, has_moved, new_field):

        # player hasn't completed task in sufficient time
        if self.current_moves >= self.max_moves:
            print('You have run out of time!')
            self.over = True
            return self.xlost

        # player has enough gold to finish the game, thus the game is over
        # for the first RL agent
        if self.get_inventory_value() + self.current_gold >= self.max_gold:
            self.over = True
            print(f'You have sufficient amout of gold: {self.get_inventory_value() + self.current_gold}, now go to the merchant!')

            return self.xwon

        # player is waiting
        if has_moved == False:
            print(f"You are waiting: {self.xplayer}!")
            return self.xplayer
        
        # player is attacked by a bandit
        if self.near_bandit(new_position, self.current_map, self.merchant):
            print(f'You are attacked by a bandit: {self.xbandit}!')
            self.update_inventory()
            return self.xbandit


        # player has moved to an undiscoverd field
        if new_field in self.undiscovered:
            prev_loot = self.get_inventory_value()
            self.update_inventory()
            curr_loot = self.get_inventory_value()
            # rwd = (curr_loot - prev_loot) * 100
            print(f'New field is: {self.xundiscovered}')
            return self.xundiscovered
        
        # player has moved to a harvested field
        if new_field in self.discovered:
            print(f'Discovered field: {self.xdiscovered}!')
            return self.xdiscovered
        
        # player has moved to an unreachable field
        if new_field in self.unreachable:
            print(f'Illegal move: {self.xunreachable}!')
            return self.xunreachable
        
        # player has moved to a villager
        if new_field == self.villager:
            prev_loot = self.get_inventory_value()
            self.update_inventory()
            curr_loot = self.get_inventory_value()
            print(f'Villager is giving you a gift: {self.xvillager}!')
            return self.xvillager

        
        # player has moved to a merchant
        if new_field == self.merchant:
            # print('Merchant is buying your items!')
            prev_gold = self.current_gold
            self.update_gold_amount()
            curr_gold = self.current_gold
            self.update_inventory()

            print(f'Merchant: {self.xmerchant * 2}')
            return self.xmerchant * 2
        
        # player has moved to the gate 
        if new_field == self.gate:
            print(f'Gate: {self.xgate}')
            return self.xgate
        

       # Agent 2 
    def agent_two_reward(self, old_position, new_position, has_moved, new_field):

        _, path = self.bfs_distance(old_position, self.merchant, self.current_map, self.bfs_not_allowed2)

        first_step = path[1]

        
        # player hasn't completed task in sufficient time
        if self.current_moves >= self.max_moves:
            print('You have run out of time!')
            self.over = True
            return self.xxlost

        # player has enough gold to finish the game, thus the game is over
        # for the second RL agent
        if self.current_gold >= 50:
            self.over = True
            print(f'You have sufficient amout of gold: {self.current_gold}, now go to the gate!')

            return self.xxwon + 1000
        
        # player is attacked by a bandit
        if self.in_bandit_range(new_position, self.current_map):
            self.update_inventory()
            print(f'You are attacked by a bandit!')
            self.over = True

        # player has moved to an undiscoverd field
        if new_field in self.undiscovered:
            self.update_inventory()
            print(f'New field!')

        # player has moved to a harvested field
        if new_field in self.discovered:
            print(f'Discovered field!')
        
        # player has moved to a unreachable field
        if new_field in self.unreachable:
            print(f'Illegal move!')
        
        # player has moved to a villager
        if new_field == self.villager:
            self.update_inventory()
            print(f'Villager is giving you a gift!')

        
        # player has moved to a merchant
        if new_field == self.merchant:
            self.update_gold_amount()
            curr_gold = self.current_gold
            self.update_inventory()

            # if curr_gold >= 50:
            #     self.over = True
            #     print(f'You have sufficient amout of gold: {curr_gold}, now go to the gate!')
            #     return self.xxwon
            self.pseudo_cnt += 1
            if self.pseudo_cnt >= 5:
                self.over = True
                print(f'Merchant sold enough, now go to the gate!')
                return self.xxwon

            print(f'Merchant: {self.xxmerchant}')
            return self.xxmerchant
        
        # player has moved to the gate 
        if new_field == self.gate:
            print(f'Gate')

        if first_step == (new_position[0], new_position[1]):
            return self.xxmerchant
        else:
            return self.xxplayer


       # Agent 3 
    def agent_three_reward(self, old_position, new_position, has_moved, new_field):

        _, path = self.bfs_distance(old_position, self.gate, self.current_map, self.bfs_not_allowed3)
        if path == None:
            self.over = True
            print('No path to the gate!')
            return self.xxwon
        
        first_step = path[1]
        
        # player hasn't completed task in sufficient time
        if self.current_moves >= self.max_moves:
            print('You have run out of time!')
            self.over = True
            return self.xxlost
        
        # player is attacked by a bandit
        if self.in_bandit_range(new_position, self.current_map):
            self.update_inventory()
            print(f'You are attacked by a bandit!')

        # player has moved to an undiscoverd field
        if new_field in self.undiscovered:
            self.update_inventory()
            print(f'New field!')

        # player has moved to a harvested field
        if new_field in self.discovered:
            print(f'Discovered field!')
        
        # player has moved to a unreachable field
        if new_field in self.unreachable:
            print(f'Illegal move!')
        
        # player has moved to a villager
        if new_field == self.villager:
            self.update_inventory()
            print(f'Villager is giving you a gift!')

        
        # player has moved to a merchant
        if new_field == self.merchant:
            self.update_gold_amount()
            self.update_inventory()
            print(f'Merchant!')
        
        # player has moved to the gate 
        if new_field == self.gate:
            self.over = True
            print(f'Gate')
            return self.xxwon

        if first_step == (new_position[0], new_position[1]):
            return self.xxmerchant
        else:
            return self.xxplayer

        
    def eval(self):
        return self.current_moves

            
        


        