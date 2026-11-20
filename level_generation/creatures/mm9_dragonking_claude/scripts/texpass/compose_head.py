#!/usr/bin/env python3
"""Head set from the 4K texture-pass retexture (2026-10-30); replaces the head half of jaw/compose_head_dk.py.

The retexture sits on the exact HeadUV of work/texpass/uv_final.blend (v 0..0.8, no rescale), so the colour goes 4K ->
2K once, the normal and roughness to 1K. Graded like the body (gentle, head AO re-baked on the new HeadUV). The mouth
strip above v 0.803 stays byte for byte the approved one in all four maps: mouth UVs did not change. Classes as
compose_head_dk.py: geometry tags, ivory horn texels by colour.
Writes the ungraded colour, runs grade_basecolor.py, and pin_tone.py finishes dragonking_head_basecolor.png."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tp

HERE = Path(__file__).resolve().parents[2]
T, W, J, B = HERE / 'textures', HERE / 'work' / 'texpass', HERE / 'meshy' / 'head_retexture_texpass', HERE / 'work' / 'before_texpass' / 'textures'
N, S, STRIP_V = 2048, 1024, 0.803
GRADE = HERE.parent / 'claude_shared' / 'grade_basecolor.py'
D = np.load(W / 'head_uv.npz')
uv, tag = D['uv'], D['tag']
mouth = (tag == 1) | (tag == 2)
head_uv = uv[~mouth]
base4 = tp.load(J / 'texture_urls_0_base_color.png')
R = base4.shape[0]
print('meshy size', base4.shape)
cov4 = tp.raster(head_uv, R) >= 0
tri2, tri1 = tp.raster(head_uv, N), tp.raster(head_uv, S)
cov2, cov1 = tri2 >= 0, tri1 >= 0
tmp = T / 'dragonking_head_basecolor_ungraded.png'
tp.save(tp.down(tp.pad(base4, cov4), N), tmp)
subprocess.run([sys.executable, str(GRADE), '--ao', str(T / 'dragonking_head_ao_2k.png'), '--fine', '1.0', '--local', '0.3',
                '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15', str(tmp)], check=True)
old_n = tp.load(HERE / 'work' / 'before_texpass' / 'textures' / 'dragonking_head_normal_1k.png')
old_mr = tp.load(HERE / 'work' / 'before_texpass' / 'textures' / 'dragonking_head_metal_rough_1k.png')
old_cl = tp.load(B / 'dragonking_head_material_classes.png', 'L')
s1 = int(round((1 - STRIP_V) * S))
nrm = tp.down(tp.pad(tp.load(J / 'texture_urls_0_normal.png'), cov4), S)
nrm[:s1] = old_n[:s1]
tp.save(nrm, T / 'dragonking_head_normal_1k.png')
rough = np.clip(tp.pad(tp.down(tp.load(J / 'texture_urls_0_roughness.png', 'L'), S), cov1), 0.45 * 255, 0.9 * 255)   # Meshy's roughness is 2K
orm = np.stack([np.full((S, S), 255.0), rough, np.zeros((S, S))], -1)
orm[:s1] = old_mr[:s1]
tp.save(orm, T / 'dragonking_head_metal_rough_1k.png')
tagmap = np.where(cov1, tag[~mouth][np.maximum(tri1, 0)], -1)
graded = tp.down(tp.load(T / 'dragonking_head_basecolor_ungraded_graded.png'), S) / 255
mx, mn = graded.max(-1), graded.min(-1)
sat = (mx - mn) / (mx + 1e-9)
classes = np.zeros((S, S), np.uint8)
classes[tagmap == 0] = 1
classes[(tagmap == 0) & (sat < 0.18) & (mx > 0.45)] = 4
classes[tagmap == 3] = 5
classes[tagmap == 4] = 6
classes[:s1] = old_cl[:s1]
Image.fromarray(classes).save(T / 'dragonking_head_material_classes.png')
names = {0: 'empty', 1: 'skin', 4: 'claw_horn', 5: 'tooth', 6: 'eye', 7: 'mouth'}
share = {names[k]: round(float((classes == k).mean()), 4) for k in names}
old_share = {names[k]: round(float((old_cl == k).mean()), 4) for k in names}
json.dump({'class_share': share, 'approved_class_share': old_share, 'head_coverage': round(float(cov2.mean()), 4)},
          open(T / 'dragonking_head_compose.json', 'w'), indent=1)
print('HEADSET', share, 'approved', old_share)
