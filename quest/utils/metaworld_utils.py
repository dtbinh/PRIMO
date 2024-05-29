import copy

import numpy as np
import robomimic.utils.file_utils as FileUtils
import robomimic.utils.obs_utils as ObsUtils
from PIL import Image
from robomimic.utils.dataset import SequenceDataset
from torch.utils.data import Dataset
import torch
import torch.nn as nn
import gymnasium
from gymnasium.envs.mujoco.mujoco_rendering import OffScreenViewer
import mujoco

from metaworld.envs import ALL_V2_ENVIRONMENTS_GOAL_OBSERVABLE


from metaworld.policies import (
    SawyerAssemblyV2Policy,
    SawyerBasketballV2Policy,
    SawyerBinPickingV2Policy,
    SawyerBoxCloseV2Policy,
    SawyerButtonPressTopdownV2Policy,
    SawyerButtonPressTopdownWallV2Policy,
    SawyerButtonPressV2Policy,
    SawyerButtonPressWallV2Policy,
    SawyerCoffeeButtonV2Policy,
    SawyerCoffeePullV2Policy,
    SawyerCoffeePushV2Policy,
    SawyerDialTurnV2Policy,
    SawyerDisassembleV2Policy,
    SawyerDoorCloseV2Policy,
    SawyerDoorLockV2Policy,
    SawyerDoorOpenV2Policy,
    SawyerDoorUnlockV2Policy,
    SawyerDrawerCloseV2Policy,
    SawyerDrawerOpenV2Policy,
    SawyerFaucetCloseV2Policy,
    SawyerFaucetOpenV2Policy,
    SawyerHammerV2Policy,
    SawyerHandInsertV2Policy,
    SawyerHandlePressSideV2Policy,
    SawyerHandlePressV2Policy,
    SawyerHandlePullSideV2Policy,
    SawyerHandlePullV2Policy,
    SawyerLeverPullV2Policy,
    SawyerPegInsertionSideV2Policy,
    SawyerPegUnplugSideV2Policy,
    SawyerPickOutOfHoleV2Policy,
    SawyerPickPlaceV2Policy,
    SawyerPickPlaceWallV2Policy,
    SawyerPlateSlideBackSideV2Policy,
    SawyerPlateSlideBackV2Policy,
    SawyerPlateSlideSideV2Policy,
    SawyerPlateSlideV2Policy,
    SawyerPushBackV2Policy,
    SawyerPushV2Policy,
    SawyerPushWallV2Policy,
    SawyerReachV2Policy,
    SawyerReachWallV2Policy,
    SawyerShelfPlaceV2Policy,
    SawyerSoccerV2Policy,
    SawyerStickPullV2Policy,
    SawyerStickPushV2Policy,
    SawyerSweepIntoV2Policy,
    SawyerSweepV2Policy,
    SawyerWindowCloseV2Policy,
    SawyerWindowOpenV2Policy,
)


_policies = dict(
    {
        "assembly-v2": SawyerAssemblyV2Policy,
        "basketball-v2": SawyerBasketballV2Policy,
        "bin-picking-v2": SawyerBinPickingV2Policy,
        "box-close-v2": SawyerBoxCloseV2Policy,
        "button-press-topdown-v2": SawyerButtonPressTopdownV2Policy,
        "button-press-topdown-wall-v2": SawyerButtonPressTopdownWallV2Policy,
        "button-press-v2": SawyerButtonPressV2Policy,
        "button-press-wall-v2": SawyerButtonPressWallV2Policy,
        "coffee-button-v2": SawyerCoffeeButtonV2Policy,
        "coffee-pull-v2": SawyerCoffeePullV2Policy,
        "coffee-push-v2": SawyerCoffeePushV2Policy,
        "dial-turn-v2": SawyerDialTurnV2Policy,
        "disassemble-v2": SawyerDisassembleV2Policy,
        "door-close-v2": SawyerDoorCloseV2Policy,
        "door-lock-v2": SawyerDoorLockV2Policy,
        "door-open-v2": SawyerDoorOpenV2Policy,
        "door-unlock-v2": SawyerDoorUnlockV2Policy,
        "drawer-close-v2": SawyerDrawerCloseV2Policy,
        "drawer-open-v2": SawyerDrawerOpenV2Policy,
        "faucet-close-v2": SawyerFaucetCloseV2Policy,
        "faucet-open-v2": SawyerFaucetOpenV2Policy,
        "hammer-v2": SawyerHammerV2Policy,
        "hand-insert-v2": SawyerHandInsertV2Policy,
        "handle-press-side-v2": SawyerHandlePressSideV2Policy,
        "handle-press-v2": SawyerHandlePressV2Policy,
        "handle-pull-v2": SawyerHandlePullV2Policy,
        "handle-pull-side-v2": SawyerHandlePullSideV2Policy,
        "peg-insert-side-v2": SawyerPegInsertionSideV2Policy,
        "lever-pull-v2": SawyerLeverPullV2Policy,
        "peg-unplug-side-v2": SawyerPegUnplugSideV2Policy,
        "pick-out-of-hole-v2": SawyerPickOutOfHoleV2Policy,
        "pick-place-v2": SawyerPickPlaceV2Policy,
        "pick-place-wall-v2": SawyerPickPlaceWallV2Policy,
        "plate-slide-back-side-v2": SawyerPlateSlideBackSideV2Policy,
        "plate-slide-back-v2": SawyerPlateSlideBackV2Policy,
        "plate-slide-side-v2": SawyerPlateSlideSideV2Policy,
        "plate-slide-v2": SawyerPlateSlideV2Policy,
        "reach-v2": SawyerReachV2Policy,
        "reach-wall-v2": SawyerReachWallV2Policy,
        "push-back-v2": SawyerPushBackV2Policy,
        "push-v2": SawyerPushV2Policy,
        "push-wall-v2": SawyerPushWallV2Policy,
        "shelf-place-v2": SawyerShelfPlaceV2Policy,
        "soccer-v2": SawyerSoccerV2Policy,
        "stick-pull-v2": SawyerStickPullV2Policy,
        "stick-push-v2": SawyerStickPushV2Policy,
        "sweep-into-v2": SawyerSweepIntoV2Policy,
        "sweep-v2": SawyerSweepV2Policy,
        "window-close-v2": SawyerWindowCloseV2Policy,
        "window-open-v2": SawyerWindowOpenV2Policy,
    }
)

def get_expert(name):
    return _policies[name]()


class MetaWorldWrapper(gymnasium.Wrapper):
    def __init__(self, 
                 name: str,
                 img_width: int = 384,
                 img_height: int = 384,
                 camera_name='corner2',
                 env_kwargs=None,):
        if env_kwargs is None:
            env_kwargs = {}
        env = ALL_V2_ENVIRONMENTS_GOAL_OBSERVABLE[f'{name}-goal-observable'](**env_kwargs)
        env._freeze_rand_vec = False
        super().__init__(env)

        self.camera_name = camera_name

        self.viewer = OffScreenViewer(
            env.model,
            env.data,
            img_width,
            img_height,
            env.mujoco_renderer.max_geom,
            env.mujoco_renderer._vopt,
        )

    def render(self, mode='rgb_array'):
        cam_id = mujoco.mj_name2id(self.env.model, 
                                mujoco.mjtObj.mjOBJ_CAMERA, 
                                self.camera_name)
        
        im = self.viewer.render(
            render_mode=mode,
            camera_id=cam_id
        )[::-1]
        return im
    
    def set_task(self, task):
        self.env.set_task(task)
        self.env._partially_observable = False

    def seed(self, seed):
        self.env.seed(seed)



# class MetaWorldWrapper(gymnasium.Wrapper):
#     def __init__(self, env):
#         # if env_kwargs is None:
#         #     env_kwargs = {}
#         # env = ALL_V2_ENVIRONMENTS_GOAL_OBSERVABLE[f'{env_name}-goal-observable'](**env_kwargs)
#         # env._freeze_rand_vec = False
#         env._partially_observable = False
#         env._freeze_rand_vec = False
#         env._set_task_called = True
#         # env.render_mode = render_mode
#         env.reset()
#         env._freeze_rand_vec = True
#         super().__init__(env)
#         self.env = env
#         self.camera_name = "corner2"
#         # self.env.model.cam_pos[2] = [0.75, 0.075, 0.7]
#         # self.env._freeze_rand_vec = False

#     def set_task(self, task):
#         self.env.set_task(task)

#     # def reset(self, **kwargs):
#     #     obs = super().reset(**kwargs).astype(np.float32)
#     #     self.env.step(np.zeros(self.env.action_space.shape))
#     #     return obs

#     # def step(self, action):
#     #     reward = 0
#     #     for _ in range(2):
#     #         obs, r, _, info = self.env.step(action.copy())
#     #         reward += r
#     #     obs = obs.astype(np.float32)
#     #     return obs, reward, False, info

#     @property
#     def unwrapped(self):
#         return self.env.unwrapped

#     def render(self, *args, **kwargs):
#         return self.env.render(
#             # offscreen=True, 
#             # resolution=(384, 384), 
#             # camera_name=self.camera_name
#         ).copy()
    
#     def seed(self, seed):
#         self.env.seed(seed)


def get_dataset(
    dataset_path,
    obs_modality,
    initialize_obs_utils=True,
    seq_len=1,
    obs_seq_len=1,
    frame_stack=1,
    filter_key=None,
    hdf5_cache_mode="low_dim",
    few_demos=None,
    *args,
    **kwargs
):
    if initialize_obs_utils:
        ObsUtils.initialize_obs_utils_with_obs_specs({"obs": obs_modality})
    all_obs_keys = []
    for modality_name, modality_list in obs_modality.items():
        all_obs_keys += modality_list
    shape_meta = FileUtils.get_shape_metadata_from_dataset(
        dataset_path=dataset_path, all_obs_keys=all_obs_keys, verbose=False
    )
    seq_len = seq_len
    filter_key = filter_key
    dataset = SequenceDataset(
        hdf5_path=dataset_path,
        obs_keys=shape_meta["all_obs_keys"],
        dataset_keys=["actions"],
        load_next_obs=False,
        frame_stack=frame_stack,
        seq_length=seq_len,  # length-10 temporal sequences
        obs_seq_length=obs_seq_len,
        pad_frame_stack=True,
        pad_seq_length=True,  # pad last obs per trajectory to ensure all sequences are sampled
        get_pad_mask=False,
        goal_mode=None,
        hdf5_cache_mode=hdf5_cache_mode,  # cache dataset in memory to avoid repeated file i/o
        hdf5_use_swmr=False,
        hdf5_normalize_obs=None,
        filter_by_attribute=filter_key,  # can optionally provide a filter key here
        few_demos=few_demos,
    )
    return dataset, shape_meta

class SequenceVLDataset(Dataset):
    def __init__(self, sequence_dataset, task_id):
        self.sequence_dataset = sequence_dataset
        self.task_id = task_id
        self.n_demos = self.sequence_dataset.n_demos
        self.total_num_sequences = self.sequence_dataset.total_num_sequences

    def __len__(self):
        return len(self.sequence_dataset)

    def __getitem__(self, idx):
        return_dict = self.sequence_dataset.__getitem__(idx)
        return_dict["task_id"] = self.task_id
        return return_dict


