from gym.envs.registration import register

register(
    id='shelem-v0',
    entry_point='src.envs:ShelemEnv',
)
# register(
#     id='shelem-extrahard-v0',
#     entry_point='src.envs:ShelemExtraHardEnv',
# )
