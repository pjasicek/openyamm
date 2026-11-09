#!/usr/bin/env python3
"""Final names, dark texel block in each image (work/dark_texel.json), head ORM flat. Project folder (from mm9_nobleman_claude)."""
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
block(T / 'nj_torso_tone.png', T / 'nj_torso_final.png', 'torso')
block(T / 'nj_limbs_tone.png', T / 'nj_limbs_final.png', 'limbs')
if (T / 'nj_head_a_raw.png').exists(): block(T / 'nj_head_a_raw.png', T / 'nj_head_final.png', 'head')
Image.fromarray(np.dstack([np.full((64, 64), 255, 'u1'), np.full((64, 64), 190, 'u1'), np.zeros((64, 64), 'u1')])).save(T / 'nj_head_orm.png')
print('FINISH done')
