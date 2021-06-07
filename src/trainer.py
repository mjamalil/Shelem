import gym

from dealer.Utils import InvalidActionError

env = gym.make('src:shelem-v0')
observation = env.reset()
for t in range(10000):
        env.render()
        action = env.action_space.sample()
        try:
            observation, reward, done, info = env.step(action)
        except InvalidActionError:
            print("Invalid action: {}".format(action))
            reward = -1
            done = False
        # print(observation, reward, done, info)
        if done:
            print("Finished after {} timesteps".format(t+1))
            break
