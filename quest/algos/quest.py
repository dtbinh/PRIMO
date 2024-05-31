import torch
import torch.nn as nn
import numpy as np
from collections import deque
# from quest.modules.v1 import *
import quest.utils.tensor_utils as TensorUtils
from quest.algos.utils.data_augmentation import *
from quest.algos.utils.rgb_modules import ResnetEncoder
from quest.algos.utils.mlp_proj import MLPProj


class QueST(nn.Module):
    def __init__(self,
                 autoencoder,
                 policy_prior,
                 image_encoder_factory,
                 proprio_encoder,
                 image_aug,
                 loss_fn,
                 n_tasks,
                 cat_obs_dim,
                 offset_loss_scale,
                 action_horizon,
                 shape_meta, 
                 device,
                 ):
        super().__init__()
        # policy_cfg = policy
        self.autoencoder = autoencoder
        self.policy_prior = policy_prior
        self.use_augmentation = image_aug is not None
        self.device = device

        self.start_token = self.policy_prior.start_token
        self.offset_loss_scale = offset_loss_scale
        self.action_horizon = action_horizon
        self.action_queue = deque(maxlen=self.action_horizon)
        self.vae_block_size = autoencoder.skill_block_size
        # self.return_offset = True if self.policy_prior.offset_layers > 0
        self.codebook_size = np.array(autoencoder.fsq_level).prod()
        
        # self.skill_vae = load_vae(skill_vae, tune_decoder=tune_decoder).to(self.device)
        # print(next(self.skill_vae.parameters()).requires_grad, 'skill_vae grad')
        # self.skill_gpt = SkillGPT(self.prior_cfg).to(self.device)

        self.task_encodings = nn.Embedding(n_tasks, self.policy_prior.n_embd)
        self.obs_proj = MLPProj(cat_obs_dim, self.policy_prior.n_embd)

        self.loss = loss_fn
        
        # observation encoders
        image_encoders = {}
        for name in shape_meta["image_inputs"]:
            image_encoders[name] = image_encoder_factory()
        self.image_encoders = nn.ModuleDict(image_encoders)
        self.proprio_encoder = proprio_encoder

        # add data augmentation for rgb inputs
        self.image_aug = image_aug

    def compute_prior_loss(self, data):
        data = self.preprocess_input(data, train_mode=True)
        
        with torch.no_grad():
            indices = self.autoencoder.get_indices(data["actions"]).long()
        context = self.obs_encode(data)
        start_tokens = (torch.ones((context.shape[0], 1))*self.start_token).long().to(self.device)
        x = torch.cat([start_tokens, indices[:,:-1]], dim=1)
        targets = indices.clone()
        
        logits, prior_loss, offset = self.policy_prior(x, context, targets)
        with torch.no_grad():
            logits = logits[:,:,:self.codebook_size]
            probs = torch.softmax(logits, dim=-1)
            sampled_indices = torch.multinomial(probs.view(-1,logits.shape[-1]),1)
            sampled_indices = sampled_indices.view(-1,logits.shape[1])
        pred_actions = self.autoencoder.decode_actions(sampled_indices)
        
        if offset is not None:
            offset = offset.view(-1, self.vae_block_size, self.act_dim)
            pred_actions = pred_actions + offset
        
        offset_loss = self.loss(pred_actions, data["actions"])
        total_loss = prior_loss + self.offset_loss_scale*offset_loss
        return total_loss, {'offset_loss': offset_loss}
    
    def compute_autoencoder_loss(self, data):
        pred, pp, pp_sample, aux_loss = self.autoencoder(data["actions"])
        loss = self.loss(pred, data["actions"])
        if self.autoencoder.vq_type == 'vq':
            loss += aux_loss
            
        info = {'pp': pp, 'pp_sample': pp_sample, 'aux_loss': aux_loss.sum()}
        return loss, info

    def preprocess_input(self, data, train_mode=True):
        if train_mode:  # apply augmentation
            if self.use_augmentation:
                img_tuple = self._get_img_tuple(data)
                aug_out = self._get_aug_output_dict(self.image_aug(img_tuple))
                for img_name in self.image_encoders.keys():
                    data["obs"][img_name] = aug_out[img_name]
            return data
        else:
            data = TensorUtils.recursive_dict_list_tuple_apply(
                data, {torch.Tensor: lambda x: x.unsqueeze(dim=1)}  # add time dimension
            )
            data["task_id"] = data["task_id"].squeeze(1)
        return data
    
    def get_action(self, data):
        self.eval()
        if len(self.action_queue) == 0:
            with torch.no_grad():
                actions = self.sample_actions(data)
                self.action_queue.extend(actions[:self.action_horizon])
        action = self.action_queue.popleft()
        return action
    
    def sample_actions(self, data):
        data = self.preprocess_input(data, train_mode=False)
        context = self.obs_encode(data)
        sampled_indices, offset = self.policy_prior.get_indices_top_k(context, self.codebook_size, self.vae_block_size)
        pred_actions = self.autoencoder.decode_actions(sampled_indices)
        pred_actions_with_offset = pred_actions + offset if offset is not None else pred_actions
        pred_actions_with_offset = pred_actions_with_offset.permute(1,0,2)
        return pred_actions_with_offset.detach().cpu().numpy()

    def obs_encode(self, data):
        ### 1. encode image
        encoded = []
        for img_name in self.image_encoders.keys():
            x = data["obs"][img_name]
            B, T, C, H, W = x.shape
            e = self.image_encoders[img_name]["encoder"](
                x.reshape(B * T, C, H, W),
                ).view(B, T, -1)
            encoded.append(e)
        # 2. add proprio info
        encoded.append(self.proprio_encoder(data["obs"]['robot_states']))  # add (B, T, H_extra)
        encoded = torch.cat(encoded, -1)  # (B, T, H_all)
        init_obs_emb = self.obs_proj(encoded)
        task_emb = self.task_encodings(data["task_id"]).unsqueeze(1)
        context = torch.cat([task_emb, init_obs_emb], dim=1)
        return context

    def reset(self):
        self.action_queue = deque(maxlen=self.action_horizon)
    
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
