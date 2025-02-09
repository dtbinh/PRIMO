import torch
import torch.nn as nn
from collections import deque
# from quest.modules.v1 import *
import quest.utils.tensor_utils as TensorUtils
from quest.utils.utils import map_tensor_to_device
import quest.utils.obs_utils as ObsUtils
import einops


from abc import ABC, abstractmethod

class Policy(nn.Module, ABC):
    '''
    Super class with some basic functionality and functions we expect
    from all policy classes in our training loop
    '''

    def __init__(self, 
                 image_encoder_factory,
                 proprio_encoder,
                 obs_proj,
                 image_aug,
                 shape_meta,
                 device
                 ):
        super().__init__()

        # observation encoders
        if image_encoder_factory is not None:
            image_encoders = {}
            for name in shape_meta["image_inputs"]:
                image_encoders[name] = image_encoder_factory()
            self.image_encoders = nn.ModuleDict(image_encoders)
            self.proprio_encoder = proprio_encoder
            self.obs_proj = obs_proj
        else:
            self.image_encoders = {}
            for name in shape_meta["image_inputs"]:
                self.image_encoders[name] = None

        # add data augmentation for rgb inputs
        self.image_aug = image_aug
        self.use_augmentation = image_aug is not None

        self.device = device

    @abstractmethod
    def compute_loss(self, data):
        raise NotImplementedError('Implement in subclass')

    @abstractmethod
    def get_optimizers(self):
        raise NotImplementedError('Implement in subclass')

    def get_schedulers(self, optimizers):
        return []
    
    def preprocess_input(self, data, train_mode=True):
        if train_mode and self.use_augmentation:  # apply augmentation
            img_tuple = self._get_img_tuple(data)
            aug_out = self._get_aug_output_dict(self.image_aug(img_tuple))
            for img_name in self.image_encoders.keys():
                data["obs"][img_name] = aug_out[img_name]
        for key in self.image_encoders:
            x = TensorUtils.to_float(data['obs'][key])
            x = x / 255.
            x = torch.clip(x, 0, 1)
            data['obs'][key] = x
        return data

    def obs_encode(self, data, reduction='cat', hwc=False):
        ### 1. encode image
        encoded = []
        for img_name in self.image_encoders.keys():
            x = data["obs"][img_name]
            
            if hwc:
                x = einops.rearrange(x, 'B T H W C -> B T C H W')
            B, T, C, H, W = x.shape
            e = self.image_encoders[img_name](
                x.reshape(B * T, C, H, W),
                ).view(B, T, -1)
            encoded.append(e)
        # 2. add proprio info
        encoded.append(self.proprio_encoder(data["obs"]['robot_states']))  # add (B, T, H_extra)
        if reduction == 'cat':
            encoded = torch.cat(encoded, -1)  # (B, T, H_all)
            obs_emb = self.obs_proj(encoded) # TODO I feel that this projection should be algorithm-specific
        elif reduction == 'stack':
            encoded = torch.stack(encoded, dim=2)
            obs_emb = self.obs_proj(encoded)
        return obs_emb
        # task_emb = self.task_encoder(data["task_id"]).unsqueeze(1)
        # if 
        # context = torch.cat([task_emb, init_obs_emb], dim=1)
        # return context

    def reset(self):
        return
    
    @abstractmethod
    def get_action(self, obs, task_id):
        raise NotImplementedError('Implement in subclass')
    

    def _get_img_tuple(self, data):
        img_tuple = tuple(
            [data["obs"][img_name] for img_name in self.image_encoders.keys()]
        )
        return img_tuple

    def _get_aug_output_dict(self, out):
        img_dict = {
            img_name: out[idx]
            for idx, img_name in enumerate(self.image_encoders.keys())
        }
        return img_dict
    
    def preprocess_dataset(self, dataset, use_tqdm=True):
        return


class ChunkPolicy(Policy):
    '''
    Super class for policies which predict chunks of actions
    '''
    def __init__(self, 
                 image_encoder_factory,
                 proprio_encoder,
                 obs_proj,
                 image_aug,
                 shape_meta,
                 action_horizon,
                 device,
                 ):
        super().__init__(
            image_encoder_factory, 
            proprio_encoder, 
            obs_proj, 
            image_aug, 
            shape_meta,
            device)

        self.action_horizon = action_horizon
        self.action_queue = None


    def reset(self):
        self.action_queue = deque(maxlen=self.action_horizon)
    
    def get_action(self, obs, task_id):
        assert self.action_queue is not None, "you need to call policy.reset() before getting actions"

        self.eval()
        if len(self.action_queue) == 0:
            for key, value in obs.items():
                if key in self.image_encoders:
                    value = ObsUtils.process_frame(value, channel_dim=3)
                obs[key] = torch.tensor(value).unsqueeze(0)
            batch = {}
            batch["obs"] = obs
            batch["task_id"] = torch.tensor([task_id], dtype=torch.long)
            batch = map_tensor_to_device(batch, self.device)

            with torch.no_grad():
                actions = self.sample_actions(batch).squeeze()
                self.action_queue.extend(actions[:self.action_horizon])
        action = self.action_queue.popleft()
        return action
    
    @abstractmethod
    def sample_actions(self, obs, task_id):
        raise NotImplementedError('Implement in subclass')

