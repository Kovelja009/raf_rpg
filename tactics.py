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
        self.current_position = self.get_player_position()
        self.current_moves = 0
        self.over = False
        
    def get_field_reward(self, field_rwd):
        reward = 0
        for rwd in field_rwd:
            reward += self.item_values[rwd]
        
        return reward/len(field_rwd)
    

    def get_player_position(self, action=None):
        url = self.url_root + "/map/full/matrix"
        response = requests.request("GET", url, headers={}, data={})
        map = response.json()

        for i, row in enumerate(map):
            for j, field in enumerate(row):
                if field == self.player:
                    if action in [[1,0,0,0,0], [0,1,0,0,0], [0,0,1,0,0], [0,0,0,1,0]]:
                        return (i, j), map[i-action[0]+action[1]][j+action[3]-action[2]]
                    else:
                        return (i, j), self.player
        print('Error: There is no player on the map!')
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

    def in_bandit_range(self, my_position):
        url = self.url_root + "/map/full/matrix"
        response = requests.request("GET", url, headers={}, data={})
        map = response.json()

        for i, row in enumerate(map):
            for j, field in enumerate(row):
                if field == self.bandit:
                    if abs(i-my_position[0]) + abs(j-my_position[1]) <= 2:
                        return True
        return False

    # TODO: check for the rewards (how to handle merchant or villager)
    # TODO: change when game is over (current implementation is that 
    # the game is over when the player has reached the gate with sufficient gold)
    def get_reward(self, old_position, new_position, has_moved, new_field):
        
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
        
        # player is waiting
        if has_moved == False:
            return -2
        
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
            # return how much gold the player has earned multiplied by the merchant rate
            # so that the agent is encouraged to sell more items
            return (curr_gold - prev_gold) * self.merchant_rate
        
        # player has moved to the gate 
        if new_field == self.gate and self.current_moves < self.max_moves:
            # with enough gold
            if self.current_gold >= 50:
                self.over = True
                return 100
            # without enough gold
            else:
                return -2
        
        # player hasn't reached the gate in sufficient time
        if self.current_moves >= self.max_moves:
            return -100
        
        # player is attacked by a bandit
        if self.in_bandit_range(new_position):
            print('You are attacked by a bandit!')
            prev_loot = self.get_inventory_value()
            self.update_inventory()
            curr_loot = self.get_inventory_value()

            # return how much loot the player has lost multiplied by the bandit rate
            # so that the agent is encouraged to avoid bandits
            return (curr_loot - prev_loot) * self.bandit_rate

        