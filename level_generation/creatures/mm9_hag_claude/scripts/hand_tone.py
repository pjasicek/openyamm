#!/usr/bin/env python3
"""Hag hands toned to her face (2026-11-02): the head + hands set keeps Yrsa's hand texels (compose_head_texpass.py copies them byte for
byte outside the head square), graded to Yrsa's reddish-brown skin; the Hag's face is paler. Every texel outside the lower-left head square
(HEAD_SCALE 0.8) is multiplied per channel by the ratio of the two faces' cheek colour, measured on identical bind-pose close-ups
(v2/scripts/head_closeups.py 'eyes' view, cheeks below the eyes): Hag 158.7/98.2/74.4 against Yrsa 129.8/75.8/63.7.
Args: <in png> <out png>"""
import sys
import numpy as np
from PIL import Image
RATIO = np.array([158.7 / 129.8, 98.2 / 75.8, 74.4 / 63.7]) * 1.1      # x1.1: in texture the hands then sit at ~0.86 of the face skin (Yrsa 0.81); they read dark in close-ups
a = np.asarray(Image.open(sys.argv[1]).convert('RGB'), np.float32); n = a.shape[0]; k = int(round(n * 0.8))
m = np.ones(a.shape[:2], bool); m[n - k:, :k] = False
a[m] = np.clip(a[m] * RATIO, 0, 255)
Image.fromarray((a + 0.5).astype('u1')).save(sys.argv[2]); print('HANDTONE', RATIO.round(3), int(m.sum()))
