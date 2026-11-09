#!/usr/bin/env python3
"""Pass 7: the new head set (1K) from Meshy's 4K paint (meshy/fre_newhead_tex_4k) on work/nh/head_uv.npz. Run from the project folder.
- base / normal / roughness: nh_compose.py (4K gutters from the nearest chart texel, one Lanczos downsample to 1K; no repaint inside the
  charts: compose_islands_fre.py's border band cut the brows and lids into blocks). The base colour is NOT graded: the gentle grade's AO multiply drew polygon-shaped dark patches on the jaw
  and neck (review/newhead/grade_cmp.png), the fault the user called "differently shaded parts".
- ORM: R = ambient occlusion from the bake on the upload (textures/nh_head_ao.png), blurred 2 px and kept mild: skin and eyes at least
  SKIN_AO (0.92), hair 1 - HAIR_K (0.4) x (1 - ao); G = roughness max(r, 0.6); B = 0 (metallic 0)."""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
E = os.environ.get; M = 'meshy/fre_newhead_tex_4k'; T = 'textures'
env = dict(os.environ, UVNPZ='work/nh/head_uv_mat.npz')
subprocess.check_call([sys.executable, 'scripts/nh_mirror_paint.py', f'{M}/texture_urls_0_base_color.png', 'work/nh/meshy_base_sym.png'])      # her right brow tail / lid from her left, at 4K
subprocess.check_call([sys.executable, 'scripts/nh_paint_fix.py', 'work/nh/meshy_base_sym.png', 'work/nh/meshy_base_fix.png'])      # round 2: crown band -> hair, jewel violet
for src, dst in (('base_color', 'nh_head_base.png'), ('normal', 'nh_head_normal.png'), ('roughness', 'nh_head_rough.png')):
    subprocess.check_call([sys.executable, 'scripts/nh_compose.py', 'work/nh/meshy_base_fix.png' if src == 'base_color' else f'{M}/texture_urls_0_{src}.png', f'{T}/{dst}', '1024'])
subprocess.check_call([sys.executable, 'scripts/nh_eyes.py', f'{T}/nh_head_base.png', f'{T}/nh_head_base.png'])      # lid shade on the eyeballs (paint only)
D = np.load('work/nh/head_uv.npz'); uv, tri, fp = D['uv'], D['tri'], D['fpiece']
cv = Image.new('L', (1024, 1024), 0); dr = ImageDraw.Draw(cv)
for f, t in enumerate(tri):
    if fp[f] == 1: dr.polygon([(float(uv[v, 0] * 1024), float((1 - uv[v, 1]) * 1024)) for v in t], fill=255)
hair = np.asarray(cv.filter(ImageFilter.MaxFilter(5)), np.float32) / 255
ao = np.asarray(Image.open(f'{T}/nh_head_ao.png').convert('L').filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
r_skin = np.maximum(ao, float(E('SKIN_AO', '0.92'))); r_hair = 1 - float(E('HAIR_K', '0.4')) * (1 - ao)
R = r_skin * (1 - hair) + r_hair * hair
G = np.maximum(np.asarray(Image.open(f'{T}/nh_head_rough.png').convert('L'), np.float32) / 255, 0.6)
Image.fromarray((np.stack([R, G, np.zeros_like(G)], -1) * 255 + .5).astype('u1')).save(f'{T}/nh_head_orm.png')
print('NH TEXTURES', f'{T}/nh_head_base.png', f'{T}/nh_head_normal.png', f'{T}/nh_head_orm.png', 'AO R p5/p50', np.percentile(R, [5, 50]).round(2))
