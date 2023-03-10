import torch as t

from .quantizer import Quantizer


def grad_scale(x, scale):
    y = x
    y_grad = x * scale
    return (y - y_grad).detach() + y_grad


def round_pass(x):
    y = x.round()
    y_grad = x
    return (y - y_grad).detach() + y_grad


class LsqWeight(Quantizer):
    def __init__(self, bit, all_positive=False, symmetric=False, per_channel=True):
        super().__init__(bit)
        self.epoch = 0

        if all_positive:
            assert not symmetric, "Positive quantization cannot be symmetric"
            # unsigned activation is quantized to [0, 2^b-1]
            self.thd_neg = 0
            self.thd_pos = 2 ** bit - 1
        else:
            if symmetric:
                # signed weight/activation is quantized to [-2^(b-1)+1, 2^(b-1)-1]
                self.thd_neg = - 2 ** (bit - 1) + 1
                self.thd_pos = 2 ** (bit - 1) - 1
            else:
                # signed weight/activation is quantized to [-2^(b-1), 2^(b-1)-1]
                self.thd_neg = - 2 ** (bit - 1)
                self.thd_pos = 2 ** (bit - 1) - 1

        self.per_channel = per_channel
        self.s = t.nn.Parameter(t.FloatTensor([1]).squeeze() / (self.thd_pos ** 0.5))

    def init_weight(self, x, *args, **kwargs):
        if self.per_channel:
            self.s.data = x.detach().abs().mean(dim=(1, 2, 3), keepdim=True) * 2 / (self.thd_pos ** 0.5)
        else:
            self.s.data = x.detach().abs().mean() * 2 / (self.thd_pos ** 0.5)

    def forward(self, x):
        s_grad_scale = 1.0 / ((self.thd_pos * x.numel()) ** 0.5)
        s_scale = grad_scale(self.s, s_grad_scale) # s와 같은데 grad scale 적용된 버전
        x = x / s_scale
        x = t.clamp(x, self.thd_neg, self.thd_pos)
        x = round_pass(x)
        x = x * s_scale
        return x


class LsqAct(Quantizer):
    def __init__(self, bit, all_positive=False, symmetric=False, per_channel=True):
        super().__init__(bit)
        self.epoch = 0

        if all_positive:
            assert not symmetric, "Positive quantization cannot be symmetric"
            # unsigned activation is quantized to [0, 2^b-1]
            self.thd_neg = 0
            self.thd_pos = 2 ** bit - 1
        else:
            if symmetric:
                # signed weight/activation is quantized to [-2^(b-1)+1, 2^(b-1)-1]
                self.thd_neg = - 2 ** (bit - 1) + 1
                self.thd_pos = 2 ** (bit - 1) - 1
            else:
                # signed weight/activation is quantized to [-2^(b-1), 2^(b-1)-1]
                self.thd_neg = - 2 ** (bit - 1)
                self.thd_pos = 2 ** (bit - 1) - 1

        self.per_channel = per_channel
        self.s = t.nn.Parameter(t.FloatTensor([1]).squeeze() / (self.thd_pos ** 0.5))

    def init_activation(self, x, *args, **kwargs):
        if self.per_channel:
            self.s.data = x.detach().abs().mean(dim=(0, 2, 3), keepdim=True) * 2 / (self.thd_pos ** 0.5)
        else:
            self.s.data = x.detach().abs().mean() * 2 / (self.thd_pos ** 0.5)

    def forward(self, x):
        if self.epoch == 0 and self.training:
            self.init_activation(x)

        s_grad_scale = 1.0 / ((self.thd_pos * x.numel()) ** 0.5)
        s_scale = grad_scale(self.s, s_grad_scale)  # s와 같은데 grad scale 적용된 버전
        x = x / s_scale
        x = t.clamp(x, self.thd_neg, self.thd_pos)
        x = round_pass(x)
        x = x * s_scale
        return x
