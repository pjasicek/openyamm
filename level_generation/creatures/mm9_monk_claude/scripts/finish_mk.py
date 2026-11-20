#!/usr/bin/env python3
"""Gentle grade of the colour, ORM, uv_tex.npz with the texture table. Run after compose_mk.py, with textures/mk_ao_2k.png baked. Project folder."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
T = Path('textures')
subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(T / 'mk_ao_2k.png'), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.04', '--saturation', '1.05', str(T / 'mk_body_raw.png')])
Path(T / 'mk_body_raw_graded.png').rename(T / 'mk_body_final.png')
ao = Image.open(T / 'mk_ao_2k.png').convert('L').resize((1024, 1024), Image.LANCZOS)
r = np.asarray(Image.open(T / 'mk_body_rough.png').convert('L').resize((1024, 1024)), np.float32) / 255; a = np.asarray(ao, np.float32) / 255
Image.fromarray((np.stack([a, np.maximum(r, 0.6), np.zeros_like(r)], -1) * 255 + .5).astype('u1')).save(T / 'mk_body_orm.png')
D = dict(np.load('work/uv_v1.npz'))
tex = {'Monk': dict(base='textures/mk_body_tone.png', normal='textures/mk_body_normal.png', orm='textures/mk_body_orm.png'),
       'MonkHead': dict(base='textures/mk_head_a_final.png', normal='textures/mk_head_normal.png', orm='textures/mk_head_orm.png')}
D['textures'] = json.dumps(tex); np.savez('work/uv_tex.npz', **D); print('FINISH')
