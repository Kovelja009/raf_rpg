##### Dizajn Agenta

*Rewards*
* Collecting Materials
	* Reward = 20 for gem
	* Reward = 6 for apple, wheat
	* Reward = 2 for wood, bones, stone
* Rewards from Peasant - Reward = expected value
* Selling Materials for Gold - Reward = 1.5x the reward of the sold item
* Reaching the Gate with Sufficient Gold - Reward = 100

* Being Attacked by the Bandit - Reward = - 75% of stolen reward
* Running Out of Seller's Budget - Reward = -10
* Unsuccessful Interaction with Seller - Reward = -5
* Moving on Harvested Fields - Reward = -2
* Game Over (too many moves) - Reward = -100
* Movement or Waiting - Reward = 0

---
* Collecting Materials
	* Same as above, -manhattan distance to villager, -inventory value
* Rewards from Peasant - Reward = expected value
* Selling Materials for Gold - no reward for selling
* Being Attacked by the Bandit = -100 for 8+1 fields around him
* Moving on Harvested Fields - Reward = -2
* Game Over (too many moves) - Reward = -100
* Movement or Waiting - Reward = 0


*Actions*
UP, DOWN, LEFT, RIGHT, WAIT

One-Hot Model

75% probability of making the best move

*States*
Information Sources:
* Get Map
* Get Inventory (JSON)
* Get Inventory Value (Includes Gold Value) 
* Get Gold Inventory Value

Information Representation:
* Map
	* [-1/0/1, -1/0/1, manhattan distance] for Peasant
	* [-1/0/1, -1/0/1, manhattan distance] for Bandit
	* [-1/0/1, -1/0/1, manhattan distance] for Seller
	* [-1/0/1, -1/0/1, manhattan distance] for Gate
	* [-1/0/1, -1/0/1, manhattan distance] for Water & Mountain Together
	* [-1/0/1, -1/0/1, manhattan distance] for Forest, Meadow & Hills Separately
* Map Alternative
	* CNN Channels for Types
	* RNN or CNN for Temporal Information? (Are moves of NPCs random or follow a pattern?)
* Represent inventory as [0, 0, 0] for 3 reward levels (maybe not needed!!!!!)
* Represent inventory value without gold (integer) 
* Represent gold value (integer)

*Reinforcement Learning Algorithm*
Deep Q Networks
Actor-Critic Method (A2C/A3C) 
Even though ACM is ultimately better here because they can handle the complexity of the state space with multiple NPCs and stuff, DQN should be used because of less compute and data needed and low effort. ACM requires lots of tunning, DQN generally works out better out of the box.
