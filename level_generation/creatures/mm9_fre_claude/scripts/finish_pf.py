#!/usr/bin/env python3
"""Gentle grade of the body colour, ORM (R baked AO, G roughness, B 0), work/uv_tex.npz with the texture table. Run after compose_pf.py with
textures/pf_ao_2k.png baked. The head set is pf_head_<tier>_final.png per tier (tier_images.py binds them), tier b in the table. Project folder."""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
T = Path('textures')
_AO = T / ('pf_ao_2k_plain.png' if (T / 'pf_ao_2k_plain.png').exists() else 'pf_ao_2k.png')      # PF4 r29: the AO with the lacing column flattened
subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(_AO), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5',
                       '--contrast', '1.06', '--saturation', '1.15', str(T / 'pf_body_raw.png')])
Path(T / 'pf_body_raw_graded.png').rename(T / 'pf_body_final.png')
def orm(ao, rough, out):
    a = np.asarray(Image.open(ao).convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    r = np.asarray(Image.open(rough).convert('L').resize((1024, 1024)), np.float32) / 255
    Image.fromarray((np.stack([a, np.maximum(r, 0.6), np.zeros_like(r)], -1) * 255 + .5).astype('u1')).save(out)
orm(T / ('pf_ao_2k_plain.png' if (T / 'pf_ao_2k_plain.png').exists() else 'pf_ao_2k.png'), T / 'pf_body_rough.png', T / 'pf_body_orm.png')
if (T / 'pf_head_ao.png').exists() and (T / 'pf_head_rough.png').exists(): orm(T / 'pf_head_ao.png', T / 'pf_head_rough.png', T / 'pf_head_orm.png')
D = dict(np.load('work/uv.npz'))
tex = {'Fre': dict(base='textures/pf_body_tone.png' if (T / 'pf_body_tone.png').exists() else 'textures/pf_body_final.png', normal='textures/pf_body_normal_plain.png' if (T / 'pf_body_normal_plain.png').exists() else 'textures/pf_body_normal.png', orm='textures/pf_body_orm.png')}
if (T / 'pf_head_b_final.png').exists():
    tex['FreHead'] = dict(base='textures/pf_head_b_face.png', normal=os.environ.get('HEADN', 'textures/pf_head_normal.png'), orm='textures/pf_head_orm.png')
if 'FreHair' in [str(x) for x in D.get('matnames', [])]:      # pass 4: PeasantF2's hair, recoloured, circlet painted (hair_tex_fre.py)
    tex['FreHair'] = dict(base='textures/fre_hair_base.png', normal='textures/fre_hair_normal.png', orm='textures/fre_hair_orm.png')
D['textures'] = json.dumps(tex); np.savez('work/uv_tex.npz', **D); print('FINISH', tex)
