from multi_agent import MultiAgent


if __name__ == "__main__":
    
    map_number = 5
    max_moves = 300
    agent = MultiAgent(map_number=map_number, max_moves=max_moves)

    while not agent.is_over():
        agent.do_action()

    print(f"Game over! Finished successfully: {agent.current_moves < max_moves}")
