""" An example of training a reinforcement learning agent on the environments in RLCard
"""
import os
import time
import torch
import datetime
import keyboard
from rlcard.agents import RandomAgent
from rlcard.utils import get_device, set_seed, tournament, reorganize, Logger
from rlcard.utils.logger import plot_curve

from rlcard.envs.registration import register

from rlcard_env.env import ShelemRlEnv

register(
    env_id='shelem-rlcard',
    entry_point='rlcard_env.env:ShelemRlEnv',
)

def train():
    seed = 4
    num_episodes = 2000
    evaluate_every = 100
    num_eval_games = 100
    algorithm = 'dqn'
    log_dir = '../../experiments/shelem_result/'
    model_path = os.path.join(log_dir, 'model.pth')
    load_model = False

    # Check whether gpu is available
    # device = get_device()
    device = torch.device("cpu")

    # Seed numpy, torch, random
    set_seed(seed)

    # Make the environment with seed
    default_config = {
        'allow_step_back': False,
        'seed': seed,
    }
    env = ShelemRlEnv(config=default_config)
    if load_model:
        agent = torch.load(model_path)
    else:
        # Initialize the agent and use random agents as opponents
        if algorithm == 'dqn':
            from rlcard.agents import DQNAgent
            agent = DQNAgent(num_actions=env.num_actions,
                             state_shape=env.state_shape[0],
                             mlp_layers=[64, 64],
                             device=device)
        elif algorithm == 'nfsp':
            from rlcard.agents import NFSPAgent
            agent = NFSPAgent(num_actions=env.num_actions,
                              state_shape=env.state_shape[0],
                              hidden_layers_sizes=[64, 64],
                              q_mlp_layers=[64, 64],
                              device=device)
        else:
            raise RuntimeError("Unsupported agent")
    agents = [agent]
    for _ in range(env.num_players):
        agents.append(RandomAgent(num_actions=env.num_actions))
    env.set_agents(agents)

    t0 = time.time()
    key_press = "idkfa"
    key_idx = 0
    # Start training
    with Logger(log_dir) as logger:
        for episode in range(num_episodes):
            if keyboard.is_pressed(key_press[key_idx]):  # if key 'q' is pressed
                key_idx += 1
                if key_idx >= len(key_press):
                    break  # finishing the loop

            if algorithm == 'nfsp':
                agents[0].sample_episode_policy()

            # Generate data from the environment
            trajectories, payoffs = env.run(is_training=True)
            print(payoffs)

            # Reorganize the data to be state, action, reward, next_state, done
            trajectories = reorganize(trajectories, payoffs)

            # Feed transitions into agent memory, and train the agent
            # Here, we assume that DQN always plays the first position
            # and the other players play randomly (if any)
            for ts in trajectories[0]:
                agent.feed(ts)

            # Evaluate the performance. Play with random agents.
            if episode % evaluate_every == 0:
                logger.log_performance(env.timestep, tournament(env, num_eval_games)[0])

        # Get the paths
        csv_path, fig_path = logger.csv_path, logger.fig_path

    t1 = time.time()
    print("elapsed time")
    elapsed_time = str(datetime.timedelta(seconds=t1-t0))
    print(elapsed_time)

    # Plot the learning curve
    plot_curve(csv_path, fig_path, algorithm)

    # Save model
    torch.save(agent, model_path)
    print('Model saved in', model_path)


train()
