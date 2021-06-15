import gym

from dealer.Utils import InvalidActionError


# env = gym.make('src:shelem-v0')
# observation = env.reset()
# for t in range(100):
#         env.render()
#         action = env.action_space.sample()
#         try:
#             observation, reward, done, info = env.step(action)
#         except InvalidActionError:
#             print("Invalid action: {}".format(action))
#             reward = -1
#             done = False
#         # print(observation, reward, done, info)
#         if done:
#             print("Finished after {} timesteps".format(t+1))
#             break

# Optional: PPO2 requires a vectorized environment to run
# the env is now wrapped automatically when passing it to the constructor
# env = DummyVecEnv([lambda: env])
# from stable_baselines.common.policies import MlpPolicy
# from stable_baselines.common.vec_env import DummyVecEnv
# from stable_baselines import PPO2

# model = PPO2(MlpPolicy, env, verbose=1)
# model.learn(total_timesteps=10000)
# obs = env.reset()
# for i in range(1000):
#     action, _states = model.predict(obs)
#     try:
#         obs, rewards, dones, info = env.step(action)
#     except InvalidActionError:
#         print("Invalid action: {}".format(action))
#         reward = -1
#         done = False
    # env.render()


from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env


# env = gym.make("Pendulum-v0")

# model = SAC("MlpPolicy", env, verbose=1)
# model.learn(total_timesteps=10000, log_interval=4)
# model.save("sac_pendulum")
#
# del model # remove to demonstrate saving and loading
#
# model = SAC.load("sac_pendulum")
env = make_vec_env('src:shelem-v0', n_envs=1)
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=int(2e5))
# print(env.observation_space.sample())
obs = env.reset()
for i in range(1000):
    # print(obs)
    action, _states = model.predict(obs, deterministic=True)
    print(action)
    obs, reward, done, info = env.step(action)

    # if done:
    #     obs = env.reset()
env.close()
