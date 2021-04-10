import gym
env = gym.make('gym_shelem:shelem-v0')
observation = env.reset()
for t in range(100):
        env.render()
        action = env.action_space.sample()
        observation, reward, done, info = env.step(action)
        print(observation, reward, done, info)
        if done:
            print("Finished after {} timesteps".format(t+1))
            break
