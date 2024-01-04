import requests
import time
import numpy as np

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
        self.current_position, _ = self.get_player_position()
        self.current_moves = 0
        self.over = False
        self.current_map = self.get_map()
        
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
    
    def x_y_manhattan_distance(self, my_position, field, map):
        distance, closest_field = self.manhattan_distance(my_position, field, map)

        if closest_field == None:
            return 100, 100, 100
        # x, y
        return closest_field[1] - my_position[1], closest_field[0] - my_position[0], distance
     

    # TODO: subject to change

    # DISCUSS:
    #   - current gold, current inventory value, seperate, or maybe cumulative
    #     (currently it is cumulative amount)?


# input: x-y do seljaka, x-y do bandita, x-y do neotkrivenog polja, x-y do nevalidnog polja, number of moves
    # David
    def neural_network_input(self, my_position, map, should_print=False):
        # x-y-distance to the closest villager
        xv, yv, _ = self.x_y_manhattan_distance(my_position, self.villager, map)
        
        # x-y-distance to the closest bandit
        xb, yb, _  = self.x_y_manhattan_distance(my_position, self.bandit, map)

        # x-y-distance to the closest undiscovered field
        xund, yund, dund = 100, 100, 100
        for elem in self.undiscovered:
            x, y, d = self.x_y_manhattan_distance(my_position, elem, map)
            if d < dund:
                xund, yund, dund = x, y, d

        # x-y-distance to the closest discovered field
        xdis, ydis, ddis = 100, 100, 100
        for elem in self.discovered:
            x, y, d = self.x_y_manhattan_distance(my_position, elem, map)
            if d < ddis:
                xdis, ydis, ddis = x, y, d

        # x-y-distance to the closest invalid field
        xinv, yinv, dinv = 100, 100, 100
        for elem in self.unreachable:
            x, y, d = self.x_y_manhattan_distance(my_position, elem, map)
            if d < dinv:
                xinv, yinv, dinv = x, y, d

        # amount of cum moves
        cum_moves = self.current_moves

        if should_print:
            print(f'Player position: {my_position}')
            print(f'Real amount of gold: {self.current_gold}')
            print(f'Inventory value: {self.get_inventory_value()}')
            print(f'Villager direction: {xv}, {yv}')
            print(f'Bandit direction: {xb}, {yb}')
            print(f'Undiscovered direction: {xund}, {yund}')
            print(f'Invalid direction: {xinv}, {yinv}')
            print(f'Cum moves: {cum_moves}')
            print('------------------------------------')

        return [xv, yv, xb, yb, xund, yund, xdis, ydis, xinv, yinv]
    





        # matrix of 5x5 around the player
        # 2 - undiscovered
        # -1 - discovered
        # -3 - unreachable
        # -2 - player
        # 3 - villager
        # -3 - bandit
        # 2 - merchant
        # -1 - gate
        # out of bounds - -3
    
    
    # conv net
    def other_input(self, my_position, map):
        
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
                        # matrix.append(self.make_row(i-2, j, map, len(map), len(map[0]), self.input_size))
                        # matrix.append(self.make_row(i-1, j, map, len(map), len(map[0]), self.input_size))
                        # matrix.append(self.make_row(i, j, map, len(map), len(map[0]), self.input_size))
                        # matrix.append(self.make_row(i+1, j, map, len(map), len(map[0]), self.input_size))
                        # matrix.append(self.make_row(i+2, j, map, len(map), len(map[0]), self.input_size))
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




    
    # NOTES:[1] game is over if player has enough gold or has run out of moves or 
    #           has reached the gate with enough gold
    #       [2] even though we might have enougn gold, merchant might not buy all of our items
    #           so we need to wait few more moves to sell the rest of the items (when merchant replenishes)
    
    
    # David 
    def get_reward(self, old_position, new_position, has_moved, new_field):

        # # player hasn't completed task in sufficient time
        # if self.current_moves >= self.max_moves:
        #     print('You have run out of time!')
        #     self.over = True
        #     return self.insufficient_moves

        # # player has enough gold to finish the game, thus the game is over
        # # for the first RL agent
        # if self.get_inventory_value() + self.current_gold >= self.max_gold:
        #     self.over = True
        #     print(f'You have sufficient amout of gold: {self.get_inventory_value() + self.current_gold}, now go and finished the game!')
        #     return 100

        # # player is waiting
        # if has_moved == False:
        #     print(f"You are waiting: {self.waiting_penalty}!")
        #     return self.waiting_penalty
        
        # # player is attacked by a bandit
        # if self.in_bandit_range(new_position, self.current_map):
        #     print(f'You are attacked by a bandit: {self.bandit_rwd}!')
        #     self.update_inventory()

        #     return self.bandit_rwd


        # # player has moved to a undiscoverd field
        # if new_field in self.undiscovered:
        #     prev_loot = self.get_inventory_value()
        #     self.update_inventory()
        #     curr_loot = self.get_inventory_value()
        #     # rwd = (curr_loot - prev_loot) * 100
        #     rwd = 100
        #     print(f'New field is: {rwd}')
        #     return rwd
        
        # # player has moved to a harvested field
        # if new_field in self.discovered:
        #     print(f'Discovered field: {self.discovered_penalty}!')
        #     return self.discovered_penalty
        
        # # player has moved to a unreachable field
        # if new_field in self.unreachable:
        #     print(f'Illegal move: {self.invalid_penalty}!')
        #     return self.invalid_penalty
        
        # # player has moved to a villager
        # if new_field == self.villager:
        #     prev_loot = self.get_inventory_value()
        #     self.update_inventory()
        #     curr_loot = self.get_inventory_value()
        #     rwd = (curr_loot - prev_loot) * self.villager_rate
        #     print(f'Villager is giving you a gift: {rwd}!')
        #     return rwd
        
        # # player has moved to a merchant
        # if new_field == self.merchant:
        #     # print('Merchant is buying your items!')
        #     prev_gold = self.current_gold
        #     self.update_gold_amount()
        #     curr_gold = self.current_gold
        #     self.update_inventory()

        #     # return how much player sold to the merchant
        #     rwd = (curr_gold - prev_gold)
        #     # rwd_scaled = rwd * 1000 - 1000
        #     rwd_scaled = -100
        #     print(f'Merchant scaled: {rwd_scaled}, but sold: {rwd}')
        #     return rwd_scaled
        
        # # player has moved to the gate 
        # if new_field == self.gate:
        #     return self.discovered_penalty


        # player hasn't completed task in sufficient time
        if self.current_moves >= self.max_moves:
            print('You have run out of time!')
            self.over = True
            return self.xlost

        # player has enough gold to finish the game, thus the game is over
        # for the first RL agent
        if self.get_inventory_value() + self.current_gold >= self.max_gold:
            self.over = True
            print(f'You have sufficient amout of gold: {self.get_inventory_value() + self.current_gold}, now go and finished the game!')

            return self.xwon

        # player is waiting
        if has_moved == False:
            print(f"You are waiting: {self.xplayer}!")
            return self.xplayer
        
        # player is attacked by a bandit
        if self.in_bandit_range(new_position, self.current_map):
            print(f'You are attacked by a bandit: {self.xbandit}!')
            self.update_inventory()
            return self.xbandit


        # player has moved to a undiscoverd field
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
        
        # player has moved to a unreachable field
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

            print(f'Merchant: {self.xmerchant}')
            return self.xmerchant
        
        # player has moved to the gate 
        if new_field == self.gate:
            print(f'Gate: {self.xgate}')
            return self.xgate
        
    def eval(self):
        return self.current_moves

            
        


        