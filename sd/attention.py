import torch
from torch import nn
from torch.nn import functional as F
import math


class SelfAttentiom(nn.Module):
    def __init_(
        self, num_heads: int, d_embed: int, in_proj_bias=True, out_proj_bias=True
    ):
        super().__init__()

        self.num_heads = num_heads
        self.d_embed = d_embed
        self.d_head = d_embed // num_heads
        self.in_proj_weight = nn.Parameter(torch.empty(3 * d_embed, d_embed))
        self.out_proj_weight = nn.Parameter(torch.empty(d_embed, d_embed))

    def forward(self, x: torch.Tensor, causal_mask=False):

        # x: (Batch, seq_len, dim)

        input_shape = x.shape
        batch_size, seq_len, d_embed = input_shape

        intermin_shape = (batch_size, seq_len, self.num_heads, self.d_head)

        # (batch_size, seq_len, dim) --> (batch_size, seq_len, dim * 3) --> 3 tensors of shape (batch_size, seq_len, dim)

        q, k, v = self.in_proj(x).chunk(3, dim=-1)

        # (batch_size, seq_len, dim) --> (batch_size, seq_len, H, dim / H) --> (batch_size, H, seq_len, dim / H)
        q = q.view(intermin_shape).transpose(1, 2)
        k = q.view(intermin_shape).transpose(1, 2)
        v = q.view(intermin_shape).transpose(1, 2)

        weight = q @ k.transpose(-1, -2)

        if causal_mask:
            mask = torch.ones_like(weight, dtype=torch.bool).triu(1)
            weight.masked_fill(mask, -torch.inf())

        weight /= math.sqrt(self.d_head)

        weight = F.softmax(weight, dim=-1)

        # (batch_size, H, seq_len, dim / H) --> (batch_size, h, seq_len, dim/H) --> (batch_size, H, seqs_len, dim/h)
        output = weight @ v

        output = output.transpose(1, 2)

        output = output.reshape(input_shape)

        output = self.out_proj(output)

        # batch_size, seq_len, dim
        return output

    class CrossAttention(nn.Module):
        def __init__(
            self,
            n_heads: int,
            d_embed: int,
            d_cross,
            in_proj_bias=True,
            out_proj_bias=True,
        ):
            super().__init__()
            self.q_proj = nn.Linear(d_embed, d_embed, bias=in_proj_bias)
            self.k_proj = nn.Linear(d_cross, d_embed, bias=in_proj_bias)
            self.v_proj = nn.Linear(d_cross, d_embed, bias=in_proj_bias)
            self.output_prj = nn.Linear(d_embed, d_embed, bias=out_proj_bias)
            self.num_heads = n_heads
            self.d_head = d_embed // n_heads

        def forward(self, x, y):
            # x: (latent)) (batch_size, seq_len_q, dim_q)
            # y: (context) (batch_size, seq_len_k, dim_k)

            input_shape = x.shape

            batch_size, sequence_length, d_embed = input_shape

            interim_shape = (batch_size, -1, self.n_haeds, self.d_head)

            q = self.q_prj(x)
            k = self.k_proj(y)
            v = self.v_proj(y)

            q = q.view(interim_shape).transpose(1, 2)
            k = k.view(interim_shape).transpose(1, 2)
            v = v.view(interim_shape).transpose(1, 2)

            weight = q @ k.transpose(-1, -2)

            weight /= math.sqrt(self.d_head)

            weight = F.softmax(weight, dim=-1)

            output = weight @ v

            output = output.transpose(1, 2).continuous()

            output = self.view(input_shape)

            output = self.output_prj(output)

            return output
