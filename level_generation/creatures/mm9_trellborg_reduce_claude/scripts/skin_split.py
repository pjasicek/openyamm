#!/usr/bin/env python3
"""Split the hair region (labels.npz reg 5) by tier A's head paint: faces whose paint reads as skin (luminance and red/green ratio
of the orange skin, sampled at 7 points per face) -> reg 9 'head skin outside the face box' (ears, nape, neck, shoulder tops).
Writes work/labels.npz in place (adds reg 9)."""
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
d = np.load(HERE / 'work/mesh_in.npz'); L = dict(np.load(HERE / 'work/labels.npz'))
im = np.asarray(Image.open(HERE.parent / 'mm9_trellborg_claude/textures/trell_head_a_final.png').convert('RGB'), np.float32) / 255
H, W = im.shape[:2]
w = d['wuv'].reshape(-1, 3, 2).copy(); w[:, :, 0] -= 2 * L['mat'][:, None]
B = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1/3, 1/3, 1/3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
uv = np.einsum('kb,fbc->fkc', B, w)
c = im[np.clip(((1 - uv[..., 1]) * H).astype(int), 0, H - 1), np.clip((uv[..., 0] * W).astype(int), 0, W - 1)]
lum = c @ [.299, .587, .114]
skin = (lum > .2) & (c[..., 0] > 1.5 * c[..., 2])
frac = skin.mean(1)
reg = L['reg'].copy(); reg[L['reg'] == 9] = 5
reg[(reg == 5) & (frac >= .5)] = 9
L['reg'] = reg
print('hair', int((reg == 5).sum()), 'skin outside the box', int((reg == 9).sum()))
np.savez(HERE / 'work/labels.npz', **L)
