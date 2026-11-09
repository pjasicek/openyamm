#!/usr/bin/env python3
"""AO crops, gentle grade of the colour, ORM, uv_tex.npz with the UVs remapped to the two half images. Run after compose_es.py. Project folder."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
T = Path('textures')
ao = Image.open(T / 'es_ao_4k.png').convert('L'); S = ao.size[0]
for part, box in (('up', (0, 0, S, S // 2)), ('low', (0, S // 2, S, S))):
    ao.resize((2048, 1024), Image.LANCZOS, box=box).save(T / f'es_{part}_ao.png')
    ao.resize((1024, 512), Image.LANCZOS, box=box).save(T / f'es_{part}_ao1k.png')
    subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(T / f'es_{part}_ao.png'), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.10', str(T / f'es_{part}_raw.png')])
    r = np.asarray(Image.open(T / f'es_{part}_rough.png').convert('L'), np.float32) / 255
    a = np.asarray(Image.open(T / f'es_{part}_ao1k.png').convert('L'), np.float32) / 255
    orm = np.stack([a, np.maximum(r, 0.5), np.zeros_like(r)], -1)
    Image.fromarray((orm * 255 + .5).astype('u1')).save(T / f'es_{part}_orm.png')
D = dict(np.load('work/uv_v1b.npz')); uv, mat, tri = D['uv'].copy(), D['mat'], D['tri']
for m in (0, 1):
    vs = np.unique(tri[mat == m])
    uv[vs, 1] = (uv[vs, 1] - (0.5 if m == 0 else 0.0)) * 2
D['uv'] = uv
tex = {'SorcererUp': dict(base='textures/es_up_tone.png', normal='textures/es_up_normal.png', orm='textures/es_up_orm.png'),
       'SorcererLow': dict(base='textures/es_low_tone.png', normal='textures/es_low_normal.png', orm='textures/es_low_orm.png'),
       'SorcererHead': dict(base='textures/es_head_b_tone.png', normal='textures/es_head_normal.png', orm='textures/es_head_orm.png')}
D['textures'] = json.dumps(tex)
np.savez('work/uv_tex.npz', **D)
print('FINISH')
