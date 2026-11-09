#!/usr/bin/env python3
"""Mouth faces of the Triton's face skin (lips and the small corner fangs; a uniform cut smoothed the fangs away):
head-skin faces of the body piece with centroid y < -0.07, 1.476 < z < 1.514 and |x + 0.007| < 0.05 -> work/mouth.npy,
and work/keep_b.npy = work/keep_a.npy | mouth. Usage: mouth_keep.py"""
import numpy as np
c = np.load('work/classes.npz', allow_pickle=True); cen, reg, piece = c['centroid'], c['region'], c['piece']
mouth = ((reg == 'head') & (piece == 0) & (cen[:, 1] < -.07) & (cen[:, 2] > 1.476) & (cen[:, 2] < 1.514)
         & (np.abs(cen[:, 0] + .007) < .05))
keep = np.load('work/keep_a.npy') | mouth
np.save('work/mouth.npy', mouth); np.save('work/keep_b.npy', keep); print('MOUTH', int(mouth.sum()), 'keep_b', int(keep.sum()))
