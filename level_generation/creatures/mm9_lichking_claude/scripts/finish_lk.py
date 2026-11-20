#!/usr/bin/env python3
"""AO grade of the body colour, ORM maps, the head set (the approved Lich's skull paint, cooled towards MM9's pale blue-grey bone, eyes kept),
the staff's procedural wood, and work/uv_tex.npz (uv npz + textures json) for build_glb_lk.py. Project folder, after compose_lk.py."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None
T = Path('textures'); LT = Path('../mm9_lich_claude/textures')
ao = Image.open(T / 'lk_ao_2k.png').convert('L')
subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(T / 'lk_ao_2k.png'), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.05', str(T / 'lk_raw.png')])
r = np.asarray(Image.open(T / 'lk_rough.png').convert('L'), np.float32) / 255
a = np.asarray(ao.resize((1024, 1024), Image.LANCZOS), np.float32) / 255
Image.fromarray((np.stack([a, np.maximum(r, 0.45), np.zeros_like(r)], -1) * 255 + .5).astype('u1')).save(T / 'lk_orm.png')
# head set: the Lich's skull paint, cooled; eyes (the Lich's eye mask) keep their embers
hb = np.asarray(Image.open(LT / 'lich_head_basecolor_graded.png').convert('RGB'), np.float32) / 255
eye = np.asarray(Image.open(LT / 'lich_eye_mask.png').convert('L').resize(hb.shape[1::-1], Image.LANCZOS), np.float32) / 255
eye = np.clip(ndimage.gaussian_filter(eye, 3) * 2.5, 0, 1)[..., None]
L = (hb @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
cool = np.clip(L * np.array([0.90, 0.98, 1.08]) * 1.04, 0, 1)
head = hb * eye + (0.25 * hb + 0.75 * cool) * (1 - eye)
Image.fromarray((np.clip(head, 0, 1) * 255 + .5).astype('u1')).save(T / 'lk_head_base.png')
for src, dst in (('lich_head_normal_1k.png', 'lk_head_normal.png'), ('lich_head_metal_rough_1k.png', 'lk_head_orm.png'), ('lich_eye_mask.png', 'lk_eye_mask.png')):
    Image.open(LT / src).save(T / dst)
# staff: dark red wood grain along v, brass bands where make_staff.py thickened the rings (9, 11) and the butt ferrule (0-2)
H, Wd = 1024, 256; rng = np.random.default_rng(7)
v = np.linspace(0, 1, H)[:, None]; u = np.linspace(0, 1, Wd)[None]
n = ndimage.gaussian_filter(rng.standard_normal((H, Wd)), (18, 1.5), mode='wrap'); n /= n.std()
grain = 0.5 + 0.5 * np.sin((u * 6 + n * 0.35 + v * 1.5) * 2 * np.pi)
wood = np.array([0.24, 0.09, 0.06]) * (0.75 + 0.35 * grain[..., None]) + 0.02 * n[..., None]
D = np.load('work/asm4.npz'); nr = int(D['staff_rings'][0]); sides = int(D['staff_rings'][1]); comp = D['comp']; names = [str(x) for x in D['names']]
s0 = np.where(comp == names.index('staff'))[0].min(); cl = D['co'][s0:s0 + nr * sides].reshape(nr, sides, 3).mean(1)
Ls = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cl, axis=0), axis=1))]; Ls /= Ls[-1]; Vr = 0.02 + 0.96 * Ls
brass = np.array([0.55, 0.40, 0.16])
band = np.zeros((H, 1))
for rr in (9, 11, 12):
    band = np.maximum(band, (np.abs(v - Vr[rr]) < 0.012).astype(float))
band = np.maximum(band, (v < Vr[2] + 0.004).astype(float))
img = wood * (1 - band[..., None]) + (brass * (0.8 + 0.3 * grain[..., None])) * band[..., None]
img[v[:, 0] > 0.985] = np.array([0.07, 0.075, 0.095]) * (0.85 + 0.3 * grain[v[:, 0] > 0.985][..., None])      # crown cap: dark steel strip
Image.fromarray((np.clip(img[::-1], 0, 1) * 255 + .5).astype('u1')).save(T / 'lk_staff_base.png')      # rows were built with v up; image row 0 is v = 1
Image.fromarray((np.stack([np.ones((H, Wd)), np.repeat(np.where(band > 0, 0.4, 0.7), Wd, 1), np.zeros((H, Wd))], -1)[::-1] * 255).astype('u1')).save(T / 'lk_staff_orm.png')
D = dict(np.load('work/uv_v1.npz'))
D['textures'] = json.dumps({'LichKing': dict(base='textures/lk_raw_graded.png', normal='textures/lk_normal.png', orm='textures/lk_orm.png'),
                            'LichKingHead': dict(base='textures/lk_head_base.png', normal='textures/lk_head_normal.png', orm='textures/lk_head_orm.png'),
                            'LichKingStaff': dict(base='textures/lk_staff_base.png', orm='textures/lk_staff_orm.png'),
                            'LichKingStaffSkull': dict(base='textures/lk_head_base.png', normal='textures/lk_head_normal.png', orm='textures/lk_head_orm.png')})
np.savez('work/uv_tex.npz', **D)
print('FINISH')
