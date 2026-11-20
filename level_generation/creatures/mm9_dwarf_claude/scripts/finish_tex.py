#!/usr/bin/env python3
"""Final names, dark texel block in each image (work/dark_texel.json), head ORM flat, weapon names. Project folder."""
import json, shutil
from pathlib import Path
import numpy as np
from PIL import Image
T = Path('textures'); D = json.load(open('work/dark_texel.json'))
def block(src, dst, k):
    a = np.array(Image.open(src).convert('RGB'))
    S = a.shape[0]; x, y = int(D[k]['u'] * S), int(D[k]['v'] * S); r = max(6, S // 100)
    a[y - r:y + r, x - r:x + r] = (92, 62, 44)
    Image.fromarray(a).save(dst)
block(T / 'dwarf_torso_a_raw_graded.png', T / 'dwarf_torso_a_final.png', 'torso')
block(T / 'dwarf_limbs_a_raw_graded.png', T / 'dwarf_limbs_a_final.png', 'limbs')
if (T / 'dwarf_head_a_raw.png').exists(): block(T / 'dwarf_head_a_raw.png', T / 'dwarf_head_a_final.png', 'head')
Image.fromarray(np.dstack([np.full((64, 64), 255, 'u1'), np.full((64, 64), 190, 'u1'), np.zeros((64, 64), 'u1')])).save(T / 'dwarf_head_orm.png')
for k in ('basecolor', 'normal', 'orm'): shutil.copy(T / f'dwarf_weapons_{k}.png', T / f'dwarf_weapons_a_{k}.png')
print('FINISH done')
