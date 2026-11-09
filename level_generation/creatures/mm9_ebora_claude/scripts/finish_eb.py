#!/usr/bin/env python3
"""AO crops, gentle grade of the colour, ORM, and work/uv_tex.npz (the body UVs remapped to the three runtime images,
plus the texture table for build_glb.py). Run after compose_eb.py. Args: <prefix ...> (first = the base tier). Project folder."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
T = Path('textures'); pres = sys.argv[1:]
import os
ao = Image.open(T / os.environ.get('AO', 'eb_ao_4k.png')).convert('L'); S = ao.size[0]; H = S // 2
SETS = (('torso', (0, H, S, S), (2048, 1024), (1024, 512)), ('head', (0, 0, H, H), (1024, 1024), (1024, 1024)),
        ('legs', (H, 0, S, H), (1024, 1024), (512, 512)))
for part, box, csize, nsize in SETS:
    ao.resize(csize, Image.LANCZOS, box=box).save(T / f'eb_{part}_ao.png')
    ao.resize(nsize, Image.LANCZOS, box=box).save(T / f'eb_{part}_aoN.png')
    for pre in pres:
        subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(T / f'eb_{part}_ao.png'), '--fine', '1.0', '--local', '0.3',
                               '--ao-strength', '0.5', '--contrast', '1.05', '--saturation', '1.06', str(T / f'{pre}_{part}_raw.png')])
    pre = pres[0]
    r = np.asarray(Image.open(T / f'{pre}_{part}_rough.png').convert('L'), np.float32) / 255
    a = np.asarray(Image.open(T / f'eb_{part}_aoN.png').convert('L'), np.float32) / 255
    orm = np.stack([a, np.maximum(r, 0.45), np.zeros_like(r)], -1)
    Image.fromarray((orm * 255 + .5).astype('u1')).save(T / f'eb_{part}_orm.png')
D = dict(np.load('work/uv_frozen.npz')); uv, mat, tri = D['uv'].copy(), D['mat'], D['tri']
for m in (0, 1, 2):
    vs = np.unique(tri[mat == m])
    if m == 0: uv[vs, 1] = uv[vs, 1] * 2
    if m == 1: uv[vs, 0] = uv[vs, 0] * 2; uv[vs, 1] = (uv[vs, 1] - 0.5) * 2
    if m == 2: uv[vs, 0] = (uv[vs, 0] - 0.5) * 2; uv[vs, 1] = (uv[vs, 1] - 0.5) * 2
D['uv'] = uv
pre = pres[0]
tex = {f'Ebora{s.capitalize()}': dict(base=f'textures/{pre}_{s}_tone.png' if pre == 'eb' else f'textures/{pre}_{s}_raw_graded.png', normal=f'textures/{pre}_{s}_normal.png', orm=f'textures/eb_{s}_orm.png') for s in ('torso', 'head', 'legs')}
if os.path.exists('textures/eb_head_pnormal.png'): tex['EboraHead']['normal'] = 'textures/eb_head_pnormal.png'
tex['EboraWing'] = dict(base='textures/eb_wing_base.png', normal='textures/eb_wing_normal.png', orm='textures/eb_wing_orm.png')
json.dump(tex, open('work/textures.json', 'w'), indent=1)
np.savez('work/uv_tex.npz', **D)
print('FINISH', pres)
