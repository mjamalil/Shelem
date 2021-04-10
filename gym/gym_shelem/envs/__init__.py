import gym
from envs.shelem_env import ShelemEnv
# from gym_shelem.envs.shelem_extrahard_env import ShelemExtraHardEnv

__package__ = "gym_shelem.envs"
__all__ = ["shelem_env"]


def register(id, entry_point, force=True):
    env_specs = gym.envs.registry.env_specs
    if id in env_specs.keys():
        if not force:
            return
        del env_specs[id]
    gym.register(
        id=id,
        entry_point=entry_point,
    )


register(
    id='shelem-v0',
    entry_point='gym_shelem.envs:ShelemEnv',
)