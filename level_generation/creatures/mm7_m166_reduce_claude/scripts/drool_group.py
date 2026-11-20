#!/usr/bin/env python3
"""Drool faces (yellow base colour on the head piece below the mouth, 967 faces) as ladder group 1 -> work/groups_drool.npy:
the thin drips lose their length first under a uniform cut (k2 r40/r35), so they get their own ratio."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f = d['faces']; uv = d['wuv'].reshape(-1, 3, 2)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
B = np.random.default_rng(0).dirichlet((1, 1, 1), 16); u = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
c = img[y, x].mean(1)
yellow = (c[:, 0] > .55) & (c[:, 1] > .45) & (c[:, 2] < .3) & (c[:, 1] > c[:, 0] * .7)
drool = yellow & (np.load('work/groups.npy') == 0) & ~np.load('work/keep_eyes.npy')
np.save('work/groups_drool.npy', drool.astype(int)); print('DROOL', int(drool.sum()))
