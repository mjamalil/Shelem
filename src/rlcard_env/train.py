""" An example of training a reinforcement learning agent on the environments in RLCard
"""
import os

import torch

import rlcard
from rlcard.agents import RandomAgent
from rlcard.utils import get_device, set_seed, tournament, reorganize, Logger
from rlcard.utils.logger import plot


from rlcard.envs.registration import register

register(
    env_id='shelem-rlcard',
    entry_point='rlcard_env.env:ShelemRlEnv',
)

def train():
    seed = 42
    num_episodes = 5000
    num_eval_games = 2000
    evaluate_every = 100
    algorithm = 'dqn'
    env = 'shelem-rlcard'
    log_dir = '../../experiments/shelem_result/'

    # Check whether gpu is available
    device = get_device()

    # Seed numpy, torch, random
    set_seed(seed)

    # Make the environment with seed
    env = rlcard.make(env, config={'seed': seed})

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
    agents = [agent]
    for _ in range(env.num_players):
        agents.append(RandomAgent(num_actions=env.num_actions))
    env.set_agents(agents)

    # Start training
    with Logger(log_dir) as logger:
        for episode in range(num_episodes):

            if algorithm == 'nfsp':
                agents[0].sample_episode_policy()

            # Generate data from the environment
            trajectories, payoffs = env.run(is_training=True)

            # Reorganaize the data to be state, action, reward, next_state, done
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

    # Plot the learning curve
    plot(csv_path, fig_path, algorithm)

    # Save model
    save_path = os.path.join(log_dir, 'model.pth')
    torch.save(agent, save_path)
    print('Model saved in', save_path)


train()
