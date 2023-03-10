import torch as t


class Quantizer(t.nn.Module):
    def __init__(self, bit):
        super().__init__()

    def init_weight(self, x, *args, **kwargs):
        pass

    def forward(self, x):
        raise NotImplementedError


class IdentityQuan(Quantizer):
    def __init__(self, bit=None, *args, **kwargs):
        super().__init__(bit)
        assert (bit is None or bit == 0), 'The bit-width of identity quantizer must be None'

    def forward(self, x):
        return x
