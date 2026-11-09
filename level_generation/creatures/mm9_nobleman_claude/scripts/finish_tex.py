#!/usr/bin/env python3
"""Final names, dark texel block in each image (work/dark_texel.json), head ORM flat. Project folder."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
T = Path('textures'); D = json.load(open('work/dark_texel.json'))
def block(src, dst, k):
    a = np.array(Image.open(src).convert('RGB'))
    S = a.shape[0]; x, y = int(D[k]['u'] * S), int(D[k]['v'] * S); r = max(6, S // 100)
    a[y - r:y + r, x - r:x + r] = (16, 11, 9)
    Image.fromarray(a).save(dst)
for t in 'abc':
    block(T / f'nb_torso_{t}_tone.png', T / f'nb_torso_{t}_final.png', 'torso')
    block(T / f'nb_head_{t}_raw.png', T / f'nb_head_{t}_final.png', 'head')
block(T / 'nb_limbs_a_raw_graded.png', T / 'nb_limbs_final.png', 'limbs')
Image.fromarray(np.dstack([np.full((64, 64), 255, 'u1'), np.full((64, 64), 190, 'u1'), np.zeros((64, 64), 'u1')])).save(T / 'nb_head_orm.png')
print('FINISH done')
