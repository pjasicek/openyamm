#!/usr/bin/env python3
"""Body images, tone per tier after the grade: Meshy's skin runs orange and bright against MM9's red-brown (A, B) and ochre (C). A gain per tier toward MM9's mean tone of bare skin, on the skin-like texels, the outfit barely moved. Writes textures/trell_body_{t}_final.png."""
import numpy as np
from PIL import Image
K = {'a': (0.90, 0.80, 0.74), 'b': (0.90, 0.80, 0.74), 'c': (0.95, 0.90, 0.78)}
for t, k in K.items():
    a = np.asarray(Image.open(f'textures/trell_body_{t}_raw_graded.png').convert('RGB'), np.float32) / 255
    s = np.clip((a[..., 0] - a[..., 2]) / np.maximum(a[..., 0], 0.05), 0, 1)     # saturation of warm tones
    w = np.clip((s - 0.45) / 0.2, 0, 1)[..., None]
    out = a * (1 - w) + (a * np.array(k, np.float32)) * w
    Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(f'textures/trell_body_{t}_final.png')
print('TONE done')
