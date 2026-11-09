#!/usr/bin/env python3
"""Reduction gate (2026-10-16): render work/<id>/tree.blend LOD0 from the eye camera at the lod_check common size
without shadows and compare with the v1 LOD0 (work/<id>/lc_stats_v1.json): front coverage and mean colour.
Usage: gate.py <id>"""
import json, os, subprocess
import numpy as np
from PIL import Image
import common
spec = common.load(); W = spec['work']
prefix = os.path.join(W, 'gate')
subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(common.TREES, 'scripts', 'render_review.py'),
                '--', spec['id'], prefix, os.path.join(W, 'tree.blend'), 'eye', 'lit', '405', 'noshadow',
                str(json.load(open(os.path.join(W, 'impostor_v1.json')))['size_m'])], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
x = np.asarray(Image.open(prefix + '_Tree_eye.png').convert('RGBA')).astype(float); m = x[..., 3] > 128
# baseline: the v1 export (work/<id>/gate_v1.json, from gate_baseline.py) rendered with this same framing
TAG = common.extra_args()[0] if common.extra_args() else 'v1'
v1 = json.load(open(os.path.join(W, f'gate_{TAG}.json')))
mean = x[m][:, :3].mean(0)
cov = m.sum() / v1['opaque_px'] - 1
d = np.abs(mean - np.array(v1['mean_rgb'])).max()
print(f"GATE {spec['id']} coverage {cov * 100:+.1f} % (<= 3), mean {mean.round(1).tolist()} vs {v1['mean_rgb']} "
      f"max diff {d:.1f} (<= 2) -> {'PASS' if abs(cov) <= 0.03 and d <= 2 else 'FAIL'}")
