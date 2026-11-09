#!/usr/bin/env python3
"""Gentle grade with the AO, ORM, the linings' dark texel, uv_tex.npz with the texture table. Project folder. Run after compose_nos.py and project_head.py."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
T = Path('textures')
G = '../claude_shared/grade_basecolor.py'
ao = Image.open(T / 'nos_ao.png').convert('L'); ao1 = ao.resize((1024, 1024), Image.LANCZOS); ao1.save(T / 'nos_ao1k.png')
subprocess.check_call([sys.executable, G, '--ao', str(T / 'nos_ao.png'), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.04', '--saturation', '1.0', str(T / 'nos_raw.png')], stdout=subprocess.DEVNULL)
subprocess.check_call([sys.executable, G, '--ao', str(T / 'nos_head_ao.png'), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.04', '--saturation', '1.0', str(T / 'nos_head_b_raw.png')], stdout=subprocess.DEVNULL)
D = dict(np.load('work/uv_final.npz')); uv, tri, mat, comp = D['uv'].copy(), D['tri'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
col = np.asarray(Image.open(T / 'nos_raw_graded.png').convert('RGB')).copy()
# the linings' texel: the middle of the largest free area, a plain dark patch
cov = np.load('work/cov_2k.npy'); e_ = cov.copy(); e_[[0, -1], :] = True; e_[:, [0, -1]] = True; d = ni.distance_transform_edt(~e_); y, x = np.unravel_index(d.argmax(), d.shape); r = int(min(d.max() - 2, 12))
print('free spot', x, y, d.max())
col[y - r:y + r, x - r:x + r] = (70, 8, 8)      # a robe-coloured patch: it takes the robe's ramp
# shoes under the robe: Meshy painted them robe red; plain dark leather, the paint's relief kept
fim = Image.new('L', (2048, 2048), 0); fdr = ImageDraw.Draw(fim)
for t in tri[(mat == 0) & (comp[tri[:, 0]] == names.index('feet'))]:
    fdr.polygon([(float(D['uv'][i, 0] * 2048), float((1 - D['uv'][i, 1]) * 2048)) for i in t], fill=255)
fm = ni.binary_dilation(np.asarray(fim) > 0, iterations=3)
gray = col.astype(np.float32).max(2) / 255
col[fm] = np.clip(gray[fm][:, None] * np.array([70, 54, 44], np.float32), 0, 255).astype('u1')
Image.fromarray(col).save(T / 'nos_final.png'); json.dump([int(x), int(y), int(r)], open('work/patch.json', 'w'))
lv = np.unique(tri[np.isin(comp[tri[:, 0]], [names.index('rlining'), names.index('slining')])])
uv[lv] = ((x + 0.5) / 2048, 1 - (y + 0.5) / 2048)
D['uv'] = uv
# plug: its charts dark in the head image
hd = np.asarray(Image.open(T / 'nos_head_b_raw_graded.png').convert('RGB')).copy(); S = hd.shape[0]
im = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(im)
for t in tri[(mat == 1) & (comp[tri[:, 0]] == names.index('plug'))]:
    dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in t], fill=255)
m = ni.binary_dilation(np.asarray(im) > 0, iterations=3); hd[m] = (14, 6, 6)
Image.fromarray(hd).save(T / 'nos_head_final.png')
lum = ni.gaussian_filter(hd.astype(np.float32).mean(2) / 255, 1.0); hp = lum - ni.gaussian_filter(lum, 7)
cvm = Image.new('L', (S, S), 0); cdr = ImageDraw.Draw(cvm)
for t in tri[mat == 1]:
    cdr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in t], fill=255)
edge_ok = ni.gaussian_filter(ni.binary_erosion(np.asarray(cvm) > 0, iterations=4).astype(np.float32), 1.5)      # no relief from the padded chart borders: they drew a star of creases on the skull
gx = ni.sobel(hp, axis=1) * 0.9 * edge_ok; gy = ni.sobel(hp, axis=0) * 0.9 * edge_ok
nn = np.dstack([-gx, gy, np.ones_like(gx)]); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
Image.fromarray(((nn * 0.5 + 0.5) * 255 + .5).astype('u1')).save(T / 'nos_head_normal.png')
r_ = np.asarray(Image.open(T / 'nos_rough.png').convert('L'), np.float32) / 255; a = np.asarray(ao1, np.float32) / 255
orm = np.stack([a, np.maximum(r_, 0.55), np.zeros_like(r_)], -1); Image.fromarray((orm * 255 + .5).astype('u1')).save(T / 'nos_orm.png')
a2 = np.asarray(Image.open(T / 'nos_head_ao.png').convert('L').resize((1024, 1024)), np.float32) / 255
orm = np.stack([a2, np.full_like(a2, 0.72), np.zeros_like(a2)], -1); Image.fromarray((orm * 255 + .5).astype('u1')).save(T / 'nos_head_orm.png')
tex = {'Nosferatu': dict(base='textures/nos_final.png', normal='textures/nos_normal.png', orm='textures/nos_orm.png'),
       'NosferatuHead': dict(base='textures/nos_head_final.png', normal='textures/nos_head_normal.png', orm='textures/nos_head_orm.png')}
D['textures'] = json.dumps(tex)
np.savez('work/uv_tex.npz', **D)
print('FINISH')
