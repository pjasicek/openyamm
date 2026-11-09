#!/usr/bin/env python3
"""Gentle grade of the body and head colour (AO from the padded bakes; the staff's charts take AO 1: it was not in the head bake), ORM
(R baked AO, G roughness >= 0.6, B 0), work/uv_tex.npz with the texture table. Project folder. Optional arg: the mesh npz (default work/uv.npz)."""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
T = Path('textures'); MESH = sys.argv[1] if len(sys.argv) > 1 else 'work/uv.npz'
U = np.load('work/uv.npz'); tri, uv, mat, comp = U['tri'], U['uv'], U['mat'], U['comp']; names = [str(x) for x in U['names']]
ao = np.asarray(Image.open(T / 'sk_head_ao.png').convert('L')).copy(); S = ao.shape[0]
im = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(im)
for t in tri[(mat == 1) & (comp[tri[:, 0]] == names.index('staff'))]: dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in t], fill=255)
from scipy import ndimage
st = ndimage.binary_dilation(np.asarray(im) > 0, iterations=3); ao[st] = 235
Image.fromarray(ao).save(T / 'sk_head_ao_fix.png')
for src, a, out in ((T / 'sk_body_fix.png', T / 'sk_ao_2k.png', T / 'sk_body_final.png'), (T / 'sk_head_fix.png', T / 'sk_head_ao_fix.png', T / 'sk_head_final.png')):
    subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(a), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5',
                           '--contrast', '1.06', '--saturation', '1.15', str(src)])
    Path(str(src)[:-4] + '_graded.png').rename(out)
def orm(ao, rough, out):
    a = np.asarray(Image.open(ao).convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    r = np.asarray(Image.open(rough).convert('L').resize((1024, 1024)), np.float32) / 255
    Image.fromarray((np.stack([a, np.maximum(r, 0.6), np.zeros_like(r)], -1) * 255 + .5).astype('u1')).save(out)
orm(T / 'sk_ao_2k.png', T / 'sk_body_rough.png', T / 'sk_body_orm.png'); orm(T / 'sk_head_ao_fix.png', T / 'sk_head_rough.png', T / 'sk_head_orm.png')
D = dict(np.load(MESH))
tex = {'Skraelos': dict(base='textures/sk_body_final.png', normal='textures/sk_body_normal.png', orm='textures/sk_body_orm.png'),
       'SkraelosHead': dict(base='textures/sk_head_final.png', normal='textures/sk_head_normal.png', orm='textures/sk_head_orm.png')}
D['textures'] = json.dumps(tex); np.savez(MESH.replace('.npz', '_tex.npz'), **D); print('FINISH', tex)
