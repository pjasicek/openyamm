#!/usr/bin/env python3
"""Gentle grade of the body colour, ORM (R baked AO, G roughness, B 0), work/uv_tex.npz with the texture table. Run after compose_pf.py with
textures/pg_ao_2k.png baked. The head set is pg_head_<tier>_final.png per tier (tier_images.py binds them), tier b in the table. Project folder."""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
T = Path('textures')
subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(T / 'pg_ao_2k.png'), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5',
                       '--contrast', '1.06', '--saturation', '1.15', str(T / 'pg_body_raw.png')])
Path(T / 'pg_body_raw_graded.png').rename(T / 'pg_body_final.png')
RMIN = float(os.environ.get('RMIN', '0.88'))     # matte skin, hair and cloth (coordinator review: waxy sheen in lit renders); the engine draws them with specular 0
def orm(ao, rough, out):
    a = np.asarray(Image.open(ao).convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    r = np.asarray(Image.open(rough).convert('L').resize((1024, 1024)), np.float32) / 255
    Image.fromarray((np.stack([a, np.maximum(r, RMIN), np.zeros_like(r)], -1) * 255 + .5).astype('u1')).save(out)
orm(T / 'pg_ao_2k.png', T / 'pg_body_rough.png', T / 'pg_body_orm.png')
HT = os.environ.get('HEAD_TIER', 'g2')        # the head set the GLB carries as its default (human GLB g2, elf GLB g1e); tier_images_pg.py swaps the colour per tier
orm(T / 'pg_head_ao.png', T / f'pg_head_{HT}_rough.png', T / f'pg_head_{HT}_orm.png')
D = dict(np.load('work/uv.npz'))
tex = {'PeasantGirl': dict(base='textures/pg_body_tone.png' if (T / 'pg_body_tone.png').exists() else 'textures/pg_body_final.png', normal='textures/pg_body_normal_fix.png' if (T / 'pg_body_normal_fix.png').exists() else 'textures/pg_body_normal.png', orm='textures/pg_body_orm.png')}
tex['PeasantGirlHead'] = dict(base=next(f'textures/pg_head_{HT}_{k}.png' for k in ('face', 'fix', 'sym') if (T / f'pg_head_{HT}_{k}.png').exists()),
                              normal=os.environ.get('HEADN', f'textures/pg_head_{HT}_normal_fix.png' if (T / f'pg_head_{HT}_normal_fix.png').exists() else f'textures/pg_head_{HT}_normal.png'), orm=f'textures/pg_head_{HT}_orm.png')
D['textures'] = json.dumps(tex); np.savez('work/uv_tex.npz', **D); print('FINISH', tex)
