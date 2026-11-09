#!/usr/bin/env python3
"""Baseline for gate.py: render the v1 export blend (work/<id>/tree_export.blend before the reduction rebuild) LOD0
from the eye camera at 405 px without shadows, framed on the v1 impostor size, into work/<id>/gate_v1.json.
Usage: gate_baseline.py <id>"""
import json, os, subprocess
import numpy as np
from PIL import Image
import common
spec = common.load(); W = spec['work']
TAG = common.extra_args()[0] if common.extra_args() else 'v1'
prefix = os.path.join(W, 'gatev1')
subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(common.TREES, 'scripts', 'render_review.py'),
                '--', spec['id'], prefix, os.path.join(W, 'tree_export.blend'), 'eye', 'lit', '405', 'noshadow',
                str(json.load(open(os.path.join(W, 'impostor_v1.json')))['size_m'])], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
x = np.asarray(Image.open(prefix + '_Tree_eye.png').convert('RGBA')).astype(float); m = x[..., 3] > 128
json.dump({'mean_rgb': x[m][:, :3].mean(0).round(2).tolist(), 'opaque_px': int(m.sum())},
          open(os.path.join(W, f'gate_{TAG}.json'), 'w'))
print('BASELINE', spec['id'], int(m.sum()), x[m][:, :3].mean(0).round(1).tolist())
