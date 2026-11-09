#!/usr/bin/env python3
"""Final names with the dark lining texel block per set (work/dark_texel.json). Project folder. Inputs: textures/pm2_{torso,limbs}_tone.png if
present else _raw_graded.png; heads pm2_head_{a,b}_tone.png if present else _raw.png."""
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
pick = lambda *c: next(T / x for x in c if (T / x).exists())
block(pick('pm2_torso_tone.png', 'pm2_torso_raw_graded.png'), T / 'pm2_torso_final.png', 'torso')
block(pick('pm2_limbs_tone.png', 'pm2_limbs_raw_graded.png'), T / 'pm2_limbs_final.png', 'limbs')
for t in 'ab':
    block(pick(f'pm2_head_{t}_tone.png', f'pm2_head_{t}_raw.png'), T / f'pm2_head_{t}_final.png', 'head')
print('FINISH done')
