import requests
import time

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
    def __init__(self, url_root, max_moves=200, max_gold=60, villager_rate=1.5, merchant_rate=0.2, bandit_rwd=-1000, lawn_rwd=['Diamond', 'Grass', 'Rice'], forest_rwd=['Stone', 'Apple', 'Wood'], highland_rwd=['Bones', 'Diamond', 'Grass', 'Wood'], villager_rwd=['Diamond', 'Rice', 'Wood']):
        self.max_moves = max_moves
        self.url_root = url_root
        self.max_gold = max_gold
        self.merchant_rate = merchant_rate
        self.villager_rate = villager_rate
        self.bandit_rwd = bandit_rwd

        self.eval_lst = []

        # Values of items
        self.item_values = {'Diamond': 20, 'Gem': 14, 'Apple': 7, 'Rice': 4, 'Stone': 3, 'Wood': 2, 'Bones': 2, 'Grass': 0}

        # Rewards for stepping on a field
        self.lawn_rwd = self.get_field_reward(lawn_rwd)
        self.forest_rwd = self.get_field_reward(forest_rwd)
        self.highland_rwd = self.get_field_reward(highland_rwd)
        self.villager_rwd = self.get_field_reward(villager_rwd)
        self.illegal_move = -100

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
            print('Error: Invalid action index!')
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


        # x, y
        return closest_field[1] - my_position[1], closest_field[0] - my_position[0], distance
     

    # TODO: subject to change

    # DISCUSS:
    #   - current gold, current inventory value, seperate, or maybe cumulative
    #     (currently it is cumulative amount)?


# input: x-y do seljaka, x-y do bandita, x-y do neotrivenog polja, x-y do nevalidnog polja, number of moves
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

        return [xv, yv, xb, yb, xund, yund, xinv, yinv]

    
    # NOTES:[1] game is over if player has enough gold or has run out of moves or 
    #           has reached the gate with enough gold
    #       [2] even though we might have enougn gold, merchant might not buy all of our items
    #           so we need to wait few more moves to sell the rest of the items (when merchant replenishes)
    
    
    # David 
    def get_reward(self, old_position, new_position, has_moved, new_field):

        # player hasn't completed task in sufficient time
        if self.current_moves >= self.max_moves:
            print('You have run out of time!')
            self.over = True
            return -100

        # player has enough gold to finish the game, thus the game is over
        # for the first RL agent
        if self.get_inventory_value() + self.current_gold >= self.max_gold:
            self.over = True
            print('You have sufficient amout of gold, now go and finished the game!')
            return 100

        # player is waiting
        if has_moved == False:
            return -1000
        
        # player is attacked by a bandit
        if self.in_bandit_range(new_position, self.current_map):
            print('You are attacked by a bandit!')
            self.update_inventory()

            return self.bandit_rwd


        # player has moved to a undiscoverd field
        if new_field in self.undiscovered:
            prev_loot = self.get_inventory_value()
            self.update_inventory()
            curr_loot = self.get_inventory_value()
            return curr_loot - prev_loot
        
        # player has moved to a harvested field
        if new_field in self.discovered:
            return -2
        
        # player has moved to a unreachable field
        if new_field in self.unreachable:
            # print('Illegal move!')
            return self.illegal_move
        
        # player has moved to a villager
        if new_field == self.villager:
            # print('Villager is giving you a gift!')
            prev_loot = self.get_inventory_value()
            self.update_inventory()
            curr_loot = self.get_inventory_value()
            return (curr_loot - prev_loot) * self.villager_rate
        
        # player has moved to a merchant
        if new_field == self.merchant:
            # print('Merchant is buying your items!')
            prev_gold = self.current_gold
            self.update_gold_amount()
            curr_gold = self.current_gold
            self.update_inventory()

            # return how much player sold to the merchant
            rwd = (curr_gold - prev_gold)
            rwd_scaled = rwd * self.merchant_rate
            # print(f'Merchant scaled: {rwd_scaled}, but sold: {rwd}')
            return rwd_scaled
        
        # player has moved to the gate 
        if new_field == self.gate:
            return -2
        
    def eval(self):
        return self.current_moves

            
        


        