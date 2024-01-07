## RPG Game Summary

### Objective
The player's goal is to collect items from reachable fields, interact with the villager for random items, and sell acquired items to the merchant for gold. Accumulate 50 gold to finish the game by reaching the gate. Avoid bandits attempting to steal items.

### Game Elements
- **Player:** Controls the main character.
- **Fields:**
  - *Reachable Fields:* Provide random items upon stepping on them.
  - *Unreachable Fields:* Inaccessible areas on the map.
- **Villager:**
  - Offers random items to the player.
- **Merchant:**
  - Buys collected items and exchanges them for gold.
- **Gate:**
  - Endpoint to finish the game once the player has gathered 50 gold.
- **Bandits:**
  - Threats attempting to steal the player's items.
 
### Multi-Agent Setup
- **Two Models:** Consist of distinct agents specialized in different tasks.
- **Model 1 - Item Collector:**
  - Focuses on efficient item collection, avoiding bandits.
- **Model 2 - Navigation Specialist:**
  - Concentrates on navigating the player to specified points.
- **Input Structure:** Both agents utilize a 3x3 matrix around the player for decision-making.
- **Collaborative Learning:** Independent operations contributing to the player's success.
---

### Multi-agent in action
![rl_raf_rpg ](https://github.com/Kovelja009/raf_rpg/assets/81018289/215fb874-223b-449d-b958-9e6834640c9a)

