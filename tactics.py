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
    def __init__(self, url_root, max_moves=500, merchant_rate=1.5, bandit_rate=0.75, lawn_rwd=['Diamond', 'Grass', 'Rice'], forest_rwd=['Stone', 'Apple', 'Wood'], highland_rwd=['Bone', 'Diamond', 'Grass', 'Wood'], villager_rwd=['Diamond', 'Rice', 'Wood']):
        self.max_moves = max_moves
        self.url_root = url_root
        self.merchant_rate = merchant_rate
        self.bandit_rate = bandit_rate

        # Values of items
        self.item_values = {'Diamond': 20, 'Gem': 14, 'Apple': 7, 'Rice': 4, 'Stone': 3, 'Wood': 2, 'Bone': 2, 'Grass': 0}

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
            self.current_inventory = {'Diamond': 0, 'Gem': 0, 'Apple': 0, 'Rice': 0, 'Stone': 0, 'Wood': 0, 'Bone': 0, 'Grass': 0}
        else:
            self.current_inventory = inventory

    def update_gold_amount(self):
        url = self.url_root + "/player/inventory/gold"
        response = requests.request("GET", url, headers={}, data={})
        self.current_gold = response.json()

    def in_bandit_range(self, my_position, map):
        print(f'My position {my_position}')
        for i, row in enumerate(map):
            for j, field in enumerate(row):
                if field == self.bandit:
                    print(i, j)
                    if abs(i-my_position[0]) + abs(j-my_position[1]) <= 2:
                        return True
        return False
    
    def manhattan_distance(self, my_position, field, map):
        closest_field = None
        closest_distance = 1000
        for i, row in enumerate(map):
            for j, f in enumerate(row):
                if f == field:
                    distance = abs(i-my_position[0]) + abs(j-my_position[1])
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_field = (i, j)

        return closest_distance, closest_field
    
    def x_y_manhattan_distance(self, my_position, field, map):
        closest_distance, closest_field = self.manhattan_distance(my_position, field, map)
        x = 0
        if my_position[1] > closest_field[1]:
            x = 1
        elif my_position[1] < closest_field[1]:
            x = -1

        y = 0
        if my_position[0] > closest_field[0]:
            y = -1
        elif my_position[0] < closest_field[0]:
            y = 1

        return x, y, closest_distance
     

    # TODO: subject to change

    # DISCUSS:
    #   - current gold, current inventory value, seperate, or maybe cumulative
    #     (currently it is cumulative amount)?


    def neural_network_input(self, my_position, map):
        # x-y-distance to the closest villager
        xv, yv, dv = self.x_y_manhattan_distance(my_position, self.villager, map)
        
        # x-y-distance to the closest merchant
        xm, ym, dm = self.x_y_manhattan_distance(my_position, self.merchant, map)

        # x-y-distance to the closest bandit
        xb, yb, db = self.x_y_manhattan_distance(my_position, self.bandit, map)

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

        # amount of cum gold (inventory + gold)
        cum_gold = self.current_gold + self.get_inventory_value()

        # amount of cum moves
        cum_moves = self.current_moves


        print(f'Villager distance: {dv}')
        print(f'Merchant distance: {dm}')
        print(f'Bandit distance: {db}')
        print(f'Undiscovered distance: {dund}')
        print(f'Invalid distance: {dinv}')
        print(f'Cum gold (inv + gold): {cum_gold}')
        print(f'Cum moves: {cum_moves}')
        print('------------------------------------')

        return [xv, yv, dv, xm, ym, dm, xb, yb, db, xund, yund, dund, xinv, yinv, dinv, cum_gold, cum_moves]

    
    # NOTES:[1] game is over if player has enough gold or has run out of moves or 
    #           has reached the gate with enough gold
    #       [2] even though we might have enougn gold, merchant might not buy all of our items
    #           so we need to wait few more moves to sell the rest of the items (when merchant replenishes)
    def get_reward(self, old_position, new_position, has_moved, new_field):

        # player hasn't reached the gate in sufficient time
        if self.current_moves >= self.max_moves:
            print('You have run out of time!')
            self.over = True
            return -100

        # player has enough gold to finish the game, thus the game is over
        # for the RL agent
        if self.current_gold >= 50:
            self.over = True
            print('You have sufficient amout of gold, now go and finished the game!')
            return 100

        # player is waiting
        if has_moved == False:
            return -2
        
        # player is attacked by a bandit
        if self.in_bandit_range(new_position, self.current_map):
            print('You are attacked by a bandit!')
            prev_loot = self.get_inventory_value()
            self.update_inventory()
            curr_loot = self.get_inventory_value()

            # return how much loot the player has lost multiplied by the bandit rate
            # so that the agent is encouraged to avoid bandits
            print(f'Bandit scaled: {(curr_loot - prev_loot) * self.bandit_rate}')
            return (curr_loot - prev_loot) * self.bandit_rate


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
            print('Illegal move!')
            return self.illegal_move
        
        # player has moved to a villager
        if new_field == self.villager:
            print('Villager is giving you a gift!')
            prev_loot = self.get_inventory_value()
            self.update_inventory()
            curr_loot = self.get_inventory_value()
            return curr_loot - prev_loot
        
        # player has moved to a merchant
        if new_field == self.merchant:
            print('Merchant is buying your items!')
            prev_gold = self.current_gold
            self.update_gold_amount()
            curr_gold = self.current_gold
            self.update_inventory()

            if self.current_gold >= 50:
                self.over = True
                print('You have sufficient amout of gold, now go and finished the game!')
                return 100

            # return how much gold the player has earned multiplied by the merchant rate
            # so that the agent is encouraged to sell more items
            print(f'Merchant scaled: {(curr_gold - prev_gold) * self.merchant_rate}, but sold: {curr_gold - prev_gold}')
            return (curr_gold - prev_gold) * self.merchant_rate
        
        # player has moved to the gate 
        if new_field == self.gate and self.current_moves < self.max_moves:
            # with enough gold
            if self.current_gold >= 50:
                self.over = True
                print('You have reached the gate and finished the whole level!')
                return 100
            # without enough gold
            else:
                return -2
            
        


        