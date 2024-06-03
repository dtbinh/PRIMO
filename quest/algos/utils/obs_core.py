"""
Contains torch Modules for core observation processing blocks
such as encoders (e.g. EncoderCore, VisualCore, ScanCore, ...)
and randomizers (e.g. Randomizer, CropRandomizer).

This file was stolen from robomimic
"""

import abc
import numpy as np
import textwrap
import random

import torch
import torch.nn as nn

import quest.utils.tensor_utils as TensorUtils
import quest.utils.obs_utils as ObsUtils

# NOTE: this is required for the backbone classes to be found by the `eval` call in the core networks
# from robomimic.models.base_nets import *
# from robomimic.utils.vis_utils import visualize_image_randomizer
# from robomimic.macros import VISUALIZE_RANDOMIZER



"""
================================================
Observation Randomizer Networks
================================================
"""
class Randomizer(nn.Module):
    """
    Base class for randomizer networks. Each randomizer should implement the @output_shape_in,
    @output_shape_out, @forward_in, and @forward_out methods. The randomizer's @forward_in
    method is invoked on raw inputs, and @forward_out is invoked on processed inputs
    (usually processed by a @VisualCore instance). Note that the self.training property
    can be used to change the randomizer's behavior at train vs. test time.
    """
    def __init__(self):
        super(Randomizer, self).__init__()

    def __init_subclass__(cls, **kwargs):
        """
        Hook method to automatically register all valid subclasses so we can keep track of valid observation randomizers
        in a global dict.

        This global dict stores mapping from observation randomizer network name to class.
        We keep track of these registries to enable automated class inference at runtime, allowing
        users to simply extend our base randomizer class and refer to that class in string form
        in their config, without having to manually register their class internally.
        This also future-proofs us for any additional randomizer classes we would
        like to add ourselves.
        """
        ObsUtils.register_randomizer(cls)

    def output_shape(self, input_shape=None):
        """
        This function is unused. See @output_shape_in and @output_shape_out.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def output_shape_in(self, input_shape=None):
        """
        Function to compute output shape from inputs to this module. Corresponds to
        the @forward_in operation, where raw inputs (usually observation modalities)
        are passed in.

        Args:
            input_shape (iterable of int): shape of input. Does not include batch dimension.
                Some modules may not need this argument, if their output does not depend
                on the size of the input, or if they assume fixed size input.

        Returns:
            out_shape ([int]): list of integers corresponding to output shape
        """
        raise NotImplementedError

    @abc.abstractmethod
    def output_shape_out(self, input_shape=None):
        """
        Function to compute output shape from inputs to this module. Corresponds to
        the @forward_out operation, where processed inputs (usually encoded observation
        modalities) are passed in.

        Args:
            input_shape (iterable of int): shape of input. Does not include batch dimension.
                Some modules may not need this argument, if their output does not depend
                on the size of the input, or if they assume fixed size input.

        Returns:
            out_shape ([int]): list of integers corresponding to output shape
        """
        raise NotImplementedError

    def forward_in(self, inputs):
        """
        Randomize raw inputs if training.
        """
        if self.training:
            randomized_inputs = self._forward_in(inputs=inputs)
            # if VISUALIZE_RANDOMIZER:
            #     num_samples_to_visualize = min(4, inputs.shape[0])
            #     self._visualize(inputs, randomized_inputs, num_samples_to_visualize=num_samples_to_visualize)
            return randomized_inputs
        else:
            return self._forward_in_eval(inputs)

    def forward_out(self, inputs):
        """
        Processing for network outputs.
        """
        if self.training:
            return self._forward_out(inputs)
        else:
            return self._forward_out_eval(inputs)

    @abc.abstractmethod
    def _forward_in(self, inputs):
        """
        Randomize raw inputs.
        """
        raise NotImplementedError

    def _forward_in_eval(self, inputs):
        """
        Test-time behavior for the randomizer
        """
        return inputs

    @abc.abstractmethod
    def _forward_out(self, inputs):
        """
        Processing for network outputs.
        """
        return inputs

    def _forward_out_eval(self, inputs):
        """
        Test-time behavior for the randomizer
        """
        return inputs

    @abc.abstractmethod
    def _visualize(self, pre_random_input, randomized_input, num_samples_to_visualize=2):
        """
        Visualize the original input and the randomized input for _forward_in for debugging purposes.
        """
        pass


class CropRandomizer(Randomizer):
    """
    Randomly sample crops at input, and then average across crop features at output.
    """
    def __init__(
        self,
        input_shape,
        crop_height=76,
        crop_width=76,
        num_crops=1,
        pos_enc=False,
    ):
        """
        Args:
            input_shape (tuple, list): shape of input (not including batch dimension)
            crop_height (int): crop height
            crop_width (int): crop width
            num_crops (int): number of random crops to take
            pos_enc (bool): if True, add 2 channels to the output to encode the spatial
                location of the cropped pixels in the source image
        """
        super(CropRandomizer, self).__init__()

        assert len(input_shape) == 3 # (C, H, W)
        assert crop_height < input_shape[1]
        assert crop_width < input_shape[2]

        self.input_shape = input_shape
        self.crop_height = crop_height
        self.crop_width = crop_width
        self.num_crops = num_crops
        self.pos_enc = pos_enc

    def output_shape_in(self, input_shape=None):
        """
        Function to compute output shape from inputs to this module. Corresponds to
        the @forward_in operation, where raw inputs (usually observation modalities)
        are passed in.

        Args:
            input_shape (iterable of int): shape of input. Does not include batch dimension.
                Some modules may not need this argument, if their output does not depend
                on the size of the input, or if they assume fixed size input.

        Returns:
            out_shape ([int]): list of integers corresponding to output shape
        """

        # outputs are shape (C, CH, CW), or maybe C + 2 if using position encoding, because
        # the number of crops are reshaped into the batch dimension, increasing the batch
        # size from B to B * N
        out_c = self.input_shape[0] + 2 if self.pos_enc else self.input_shape[0]
        return [out_c, self.crop_height, self.crop_width]

    def output_shape_out(self, input_shape=None):
        """
        Function to compute output shape from inputs to this module. Corresponds to
        the @forward_out operation, where processed inputs (usually encoded observation
        modalities) are passed in.

        Args:
            input_shape (iterable of int): shape of input. Does not include batch dimension.
                Some modules may not need this argument, if their output does not depend
                on the size of the input, or if they assume fixed size input.

        Returns:
            out_shape ([int]): list of integers corresponding to output shape
        """

        # since the forward_out operation splits [B * N, ...] -> [B, N, ...]
        # and then pools to result in [B, ...], only the batch dimension changes,
        # and so the other dimensions retain their shape.
        return list(input_shape)

    def _forward_in(self, inputs):
        """
        Samples N random crops for each input in the batch, and then reshapes
        inputs to [B * N, ...].
        """
        assert len(inputs.shape) >= 3 # must have at least (C, H, W) dimensions
        out, _ = ObsUtils.sample_random_image_crops(
            images=inputs,
            crop_height=self.crop_height,
            crop_width=self.crop_width,
            num_crops=self.num_crops,
            pos_enc=self.pos_enc,
        )
        # [B, N, ...] -> [B * N, ...]
        return TensorUtils.join_dimensions(out, 0, 1)

    def _forward_in_eval(self, inputs):
        """
        Do center crops during eval
        """
        assert len(inputs.shape) >= 3 # must have at least (C, H, W) dimensions
        inputs = inputs.permute(*range(inputs.dim()-3), inputs.dim()-2, inputs.dim()-1, inputs.dim()-3)
        out = ObsUtils.center_crop(inputs, self.crop_height, self.crop_width)
        out = out.permute(*range(out.dim()-3), out.dim()-1, out.dim()-3, out.dim()-2)
        return out

    def _forward_out(self, inputs):
        """
        Splits the outputs from shape [B * N, ...] -> [B, N, ...] and then average across N
        to result in shape [B, ...] to make sure the network output is consistent with
        what would have happened if there were no randomization.
        """
        batch_size = (inputs.shape[0] // self.num_crops)
        out = TensorUtils.reshape_dimensions(inputs, begin_axis=0, end_axis=0,
                                             target_dims=(batch_size, self.num_crops))
        return out.mean(dim=1)

    def _visualize(self, pre_random_input, randomized_input, num_samples_to_visualize=2):
        batch_size = pre_random_input.shape[0]
        random_sample_inds = torch.randint(0, batch_size, size=(num_samples_to_visualize,))
        pre_random_input_np = TensorUtils.to_numpy(pre_random_input)[random_sample_inds]
        randomized_input = TensorUtils.reshape_dimensions(
            randomized_input,
            begin_axis=0,
            end_axis=0,
            target_dims=(batch_size, self.num_crops)
        )  # [B * N, ...] -> [B, N, ...]
        randomized_input_np = TensorUtils.to_numpy(randomized_input[random_sample_inds])

        pre_random_input_np = pre_random_input_np.transpose((0, 2, 3, 1))  # [B, C, H, W] -> [B, H, W, C]
        randomized_input_np = randomized_input_np.transpose((0, 1, 3, 4, 2))  # [B, N, C, H, W] -> [B, N, H, W, C]

        # visualize_image_randomizer(
        #     pre_random_input_np,
        #     randomized_input_np,
        #     randomizer_name='{}'.format(str(self.__class__.__name__))
        # )

    def __repr__(self):
        """Pretty print network."""
        header = '{}'.format(str(self.__class__.__name__))
        msg = header + "(input_shape={}, crop_size=[{}, {}], num_crops={})".format(
            self.input_shape, self.crop_height, self.crop_width, self.num_crops)
        return msg


# class ColorRandomizer(Randomizer):
#     """
#     Randomly sample color jitter at input, and then average across color jtters at output.
#     """
#     def __init__(
#         self,
#         input_shape,
#         brightness=0.3,
#         contrast=0.3,
#         saturation=0.3,
#         hue=0.3,
#         num_samples=1,
#     ):
#         """
#         Args:
#             input_shape (tuple, list): shape of input (not including batch dimension)
#             brightness (None or float or 2-tuple): How much to jitter brightness. brightness_factor is chosen uniformly
#                 from [max(0, 1 - brightness), 1 + brightness] or the given [min, max]. Should be non negative numbers.
#             contrast (None or float or 2-tuple): How much to jitter contrast. contrast_factor is chosen uniformly
#                 from [max(0, 1 - contrast), 1 + contrast] or the given [min, max]. Should be non negative numbers.
#             saturation (None or float or 2-tuple): How much to jitter saturation. saturation_factor is chosen uniformly
#                 from [max(0, 1 - saturation), 1 + saturation] or the given [min, max]. Should be non negative numbers.
#             hue (None or float or 2-tuple): How much to jitter hue. hue_factor is chosen uniformly from [-hue, hue] or
#                 the given [min, max]. Should have 0<= hue <= 0.5 or -0.5 <= min <= max <= 0.5. To jitter hue, the pixel
#                 values of the input image has to be non-negative for conversion to HSV space; thus it does not work
#                 if you normalize your image to an interval with negative values, or use an interpolation that
#                 generates negative values before using this function.
#             num_samples (int): number of random color jitters to take
#         """
#         super(ColorRandomizer, self).__init__()

#         assert len(input_shape) == 3 # (C, H, W)

#         self.input_shape = input_shape
#         self.brightness = [max(0, 1 - brightness), 1 + brightness] if type(brightness) in {float, int} else brightness
#         self.contrast = [max(0, 1 - contrast), 1 + contrast] if type(contrast) in {float, int} else contrast
#         self.saturation = [max(0, 1 - saturation), 1 + saturation] if type(saturation) in {float, int} else saturation
#         self.hue = [-hue, hue] if type(hue) in {float, int} else hue
#         self.num_samples = num_samples

#     @torch.jit.unused
#     def get_transform(self):
#         """
#         Get a randomized transform to be applied on image.

#         Implementation taken directly from:

#         https://github.com/pytorch/vision/blob/2f40a483d73018ae6e1488a484c5927f2b309969/torchvision/transforms/transforms.py#L1053-L1085

#         Returns:
#             Transform: Transform which randomly adjusts brightness, contrast and
#             saturation in a random order.
#         """
#         transforms = []

#         if self.brightness is not None:
#             brightness_factor = random.uniform(self.brightness[0], self.brightness[1])
#             transforms.append(Lambda(lambda img: TVF.adjust_brightness(img, brightness_factor)))

#         if self.contrast is not None:
#             contrast_factor = random.uniform(self.contrast[0], self.contrast[1])
#             transforms.append(Lambda(lambda img: TVF.adjust_contrast(img, contrast_factor)))

#         if self.saturation is not None:
#             saturation_factor = random.uniform(self.saturation[0], self.saturation[1])
#             transforms.append(Lambda(lambda img: TVF.adjust_saturation(img, saturation_factor)))

#         if self.hue is not None:
#             hue_factor = random.uniform(self.hue[0], self.hue[1])
#             transforms.append(Lambda(lambda img: TVF.adjust_hue(img, hue_factor)))

#         random.shuffle(transforms)
#         transform = Compose(transforms)

#         return transform

#     def get_batch_transform(self, N):
#         """
#         Generates a batch transform, where each set of sample(s) along the batch (first) dimension will have the same
#         @N unique ColorJitter transforms applied.

#         Args:
#             N (int): Number of ColorJitter transforms to apply per set of sample(s) along the batch (first) dimension

#         Returns:
#             Lambda: Aggregated transform which will autoamtically apply a different ColorJitter transforms to
#                 each sub-set of samples along batch dimension, assumed to be the FIRST dimension in the inputted tensor
#                 Note: This function will MULTIPLY the first dimension by N
#         """
#         return Lambda(lambda x: torch.stack([self.get_transform()(x_) for x_ in x for _ in range(N)]))

#     def output_shape_in(self, input_shape=None):
#         # outputs are same shape as inputs
#         return list(input_shape)

#     def output_shape_out(self, input_shape=None):
#         # since the forward_out operation splits [B * N, ...] -> [B, N, ...]
#         # and then pools to result in [B, ...], only the batch dimension changes,
#         # and so the other dimensions retain their shape.
#         return list(input_shape)

#     def _forward_in(self, inputs):
#         """
#         Samples N random color jitters for each input in the batch, and then reshapes
#         inputs to [B * N, ...].
#         """
#         assert len(inputs.shape) >= 3 # must have at least (C, H, W) dimensions

#         # Make sure shape is exactly 4
#         if len(inputs.shape) == 3:
#             inputs = torch.unsqueeze(inputs, dim=0)

#         # TODO: Make more efficient other than implicit for-loop?
#         # Create lambda to aggregate all color randomizings at once
#         transform = self.get_batch_transform(N=self.num_samples)

#         return transform(inputs)

#     def _forward_out(self, inputs):
#         """
#         Splits the outputs from shape [B * N, ...] -> [B, N, ...] and then average across N
#         to result in shape [B, ...] to make sure the network output is consistent with
#         what would have happened if there were no randomization.
#         """
#         batch_size = (inputs.shape[0] // self.num_samples)
#         out = TensorUtils.reshape_dimensions(inputs, begin_axis=0, end_axis=0,
#                                              target_dims=(batch_size, self.num_samples))
#         return out.mean(dim=1)

#     def _visualize(self, pre_random_input, randomized_input, num_samples_to_visualize=2):
#         batch_size = pre_random_input.shape[0]
#         random_sample_inds = torch.randint(0, batch_size, size=(num_samples_to_visualize,))
#         pre_random_input_np = TensorUtils.to_numpy(pre_random_input)[random_sample_inds]
#         randomized_input = TensorUtils.reshape_dimensions(
#             randomized_input,
#             begin_axis=0,
#             end_axis=0,
#             target_dims=(batch_size, self.num_samples)
#         )  # [B * N, ...] -> [B, N, ...]
#         randomized_input_np = TensorUtils.to_numpy(randomized_input[random_sample_inds])

#         pre_random_input_np = pre_random_input_np.transpose((0, 2, 3, 1))  # [B, C, H, W] -> [B, H, W, C]
#         randomized_input_np = randomized_input_np.transpose((0, 1, 3, 4, 2))  # [B, N, C, H, W] -> [B, N, H, W, C]

#         visualize_image_randomizer(
#             pre_random_input_np,
#             randomized_input_np,
#             randomizer_name='{}'.format(str(self.__class__.__name__))
#         )

#     def __repr__(self):
#         """Pretty print network."""
#         header = '{}'.format(str(self.__class__.__name__))
#         msg = header + f"(input_shape={self.input_shape}, brightness={self.brightness}, contrast={self.contrast}, " \
#                        f"saturation={self.saturation}, hue={self.hue}, num_samples={self.num_samples})"
#         return msg


class GaussianNoiseRandomizer(Randomizer):
    """
    Randomly sample gaussian noise at input, and then average across noises at output.
    """
    def __init__(
        self,
        input_shape,
        noise_mean=0.0,
        noise_std=0.3,
        limits=None,
        num_samples=1,
    ):
        """
        Args:
            input_shape (tuple, list): shape of input (not including batch dimension)
            noise_mean (float): Mean of noise to apply
            noise_std (float): Standard deviation of noise to apply
            limits (None or 2-tuple): If specified, should be the (min, max) values to clamp all noisied samples to
            num_samples (int): number of random color jitters to take
        """
        super(GaussianNoiseRandomizer, self).__init__()

        self.input_shape = input_shape
        self.noise_mean = noise_mean
        self.noise_std = noise_std
        self.limits = limits
        self.num_samples = num_samples

    def output_shape_in(self, input_shape=None):
        # outputs are same shape as inputs
        return list(input_shape)

    def output_shape_out(self, input_shape=None):
        # since the forward_out operation splits [B * N, ...] -> [B, N, ...]
        # and then pools to result in [B, ...], only the batch dimension changes,
        # and so the other dimensions retain their shape.
        return list(input_shape)

    def _forward_in(self, inputs):
        """
        Samples N random gaussian noises for each input in the batch, and then reshapes
        inputs to [B * N, ...].
        """
        out = TensorUtils.repeat_by_expand_at(inputs, repeats=self.num_samples, dim=0)

        # Sample noise across all samples
        out = torch.rand(size=out.shape) * self.noise_std + self.noise_mean + out

        # Possibly clamp
        if self.limits is not None:
            out = torch.clip(out, min=self.limits[0], max=self.limits[1])

        return out

    def _forward_out(self, inputs):
        """
        Splits the outputs from shape [B * N, ...] -> [B, N, ...] and then average across N
        to result in shape [B, ...] to make sure the network output is consistent with
        what would have happened if there were no randomization.
        """
        batch_size = (inputs.shape[0] // self.num_samples)
        out = TensorUtils.reshape_dimensions(inputs, begin_axis=0, end_axis=0,
                                             target_dims=(batch_size, self.num_samples))
        return out.mean(dim=1)

    def _visualize(self, pre_random_input, randomized_input, num_samples_to_visualize=2):
        batch_size = pre_random_input.shape[0]
        random_sample_inds = torch.randint(0, batch_size, size=(num_samples_to_visualize,))
        pre_random_input_np = TensorUtils.to_numpy(pre_random_input)[random_sample_inds]
        randomized_input = TensorUtils.reshape_dimensions(
            randomized_input,
            begin_axis=0,
            end_axis=0,
            target_dims=(batch_size, self.num_samples)
        )  # [B * N, ...] -> [B, N, ...]
        randomized_input_np = TensorUtils.to_numpy(randomized_input[random_sample_inds])

        pre_random_input_np = pre_random_input_np.transpose((0, 2, 3, 1))  # [B, C, H, W] -> [B, H, W, C]
        randomized_input_np = randomized_input_np.transpose((0, 1, 3, 4, 2))  # [B, N, C, H, W] -> [B, N, H, W, C]

        # visualize_image_randomizer(
        #     pre_random_input_np,
        #     randomized_input_np,
        #     randomizer_name='{}'.format(str(self.__class__.__name__))
        # )

    def __repr__(self):
        """Pretty print network."""
        header = '{}'.format(str(self.__class__.__name__))
        msg = header + f"(input_shape={self.input_shape}, noise_mean={self.noise_mean}, noise_std={self.noise_std}, " \
                       f"limits={self.limits}, num_samples={self.num_samples})"
        return msg
