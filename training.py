from model import DeepQNet, DQNTrainer
from openai_gym import RafRpg
import torch
import time


# promeniti input (koje informacije se prosledjuju mrezi) - x, y udaljenost samo
# promeniti reward? -> promeniti fiksnu nagradu za bandita
# promeniti model -> uprostili ga
# uvesti metriku za merenje modela
# raditi u batchevima

#########################################

# promeniti nagradu za seljaka i novac uvezati u jednu nagradu

# reward = reward - dist(merchant) - (2/55)*inventory_value (bude oko 50)

# reward = reward/inventory_value

# kada je inventar manji od ~50, treba da nam se isplati da skupkljamo stvari
# kada je inventar veci od ~50, treba da nam se isplati da idemo kod trgovca

#########################################
# hiperparametri: lr, gamma, broj epoha, broj koraka po epohi


#########################################
#########################################

# ideja: 2 mreze, jedna za nagrade, jedna da ode do trgovca
# I mreza: cilj je da se sto brze stigne do 60 zlata
# kraj je kada stigne do 60 zlata ili istekne vreme
# input: x-y do seljaka, x-y do bandita, x-y do neotrivenog polja, x-y do nevalidnog polja, number of moves
# 



if __name__ == "__main__":
    game = RafRpg()
    input = game.tactics.neural_network_input(game.tactics.current_position, game.tactics.current_map)
    model = DeepQNet(len(input), 5)
    trainer = DQNTrainer(model, lr=0.005, gamma=0.95)
    epochs = 200
    should_print = False
    model_over_epochs = []
    file_path = "logs.txt"
    for i in range(epochs):
        game.reset()
        start_time = time.time()
        print('\n')

        while not game.tactics.over:
            # if game.tactics.current_moves % 10 == 0:
            #     print("#################")
            #     print(game.tactics.current_map)
            #     print("#################")
            #     should_print = True
            # else:
            #     should_print = False

            old_input = game.tactics.neural_network_input(game.tactics.current_position, game.tactics.current_map, should_print=should_print)
            action = trainer.model(torch.tensor(old_input, dtype=torch.float))
            action_idx = torch.argmax(action).item()
            action = game.tactics.convert_idx_to_action(action_idx)
            map, reward, done, _ = game.step(action)

            # NOTE: reward is decreased for each move
            reward -= (0.2*game.tactics.current_moves)
            if should_print:
                print(f"Epoch: {i}")
                print(f"Reward: {reward}")
            new_input = game.tactics.neural_network_input(game.tactics.current_position, game.tactics.current_map, should_print=should_print)
            trainer.train_step(old_input, action, reward, new_input, done)

            if game.tactics.current_moves % 10 == 0:
                game.tactics.eval()
        
        end_time = time.time()
        metric = game.tactics.eval()
        model_over_epochs.append(metric)
        # save model in logs.txt
        with open(file_path, "a") as f:
            f.write(f"{metric}, {i}\n")
        print(f"Epoch {i} finished in {end_time - start_time} seconds")
        print(f"Epoch Metric: {metric}")

    last = 9
    overall_metric = sum(model_over_epochs)/len(model_over_epochs)
    print(f"Overall metric: {overall_metric}")
    trainer.model.save()
    # 92
    # 70
    # 33 (big network, (192, 128), big lr (0.01))
