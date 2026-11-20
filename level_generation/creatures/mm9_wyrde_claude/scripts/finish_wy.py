#!/usr/bin/env python3
"""Gentle grade of the body colour, ORM (R baked AO, G roughness, B 0), work/uv_tex.npz with the texture table. Run after compose_pf.py with
textures/wy_ao_2k.png baked. The head set is wy_head_<tier>_final.png per tier (tier_images.py binds them), tier b in the table. Project folder."""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
T = Path('textures')
subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(T / 'wy_ao_2k.png'), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5',
                       '--contrast', '1.06', '--saturation', '1.15', str(T / 'wy_body_raw.png')])
Path(T / 'wy_body_raw_graded.png').rename(T / 'wy_body_final.png')
def orm(ao, rough, out):
    a = np.asarray(Image.open(ao).convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    r = np.asarray(Image.open(rough).convert('L').resize((1024, 1024)), np.float32) / 255
    Image.fromarray((np.stack([a, np.maximum(r, 0.6), np.zeros_like(r)], -1) * 255 + .5).astype('u1')).save(out)
orm(T / 'wy_ao_2k.png', T / 'wy_body_rough.png', T / 'wy_body_orm.png')
if (T / 'wy_head_ao.png').exists() and (T / 'wy_head_rough.png').exists(): orm(T / 'wy_head_ao.png', T / 'wy_head_rough.png', T / 'wy_head_orm.png')
D = dict(np.load('work/uv.npz'))
tex = {'Wyrde': dict(base='textures/wy_body_tone.png' if (T / 'wy_body_tone.png').exists() else 'textures/wy_body_final.png', normal='textures/wy_body_normal.png', orm='textures/wy_body_orm.png')}
if (T / 'wy_head_y_final.png').exists():
    tex['WyrdeHead'] = dict(base='textures/wy_head_y_final.png', normal=os.environ.get('HEADN', 'textures/wy_head_normal.png'), orm='textures/wy_head_orm.png')
D['textures'] = json.dumps(tex); np.savez('work/uv_tex.npz', **D); print('FINISH', tex)
