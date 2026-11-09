#!/usr/bin/env python3
"""Largest difference of every joint's global position and of the polearm tip (+1.2 m along the shaft) between two
GLBs of the same rig, per clip, sampled at 48 Hz. Usage: compare_clips.py <a.glb> <b.glb>"""
import sys
import numpy as np
from gltf_pose import Gltf
a, b = Gltf(sys.argv[1]), Gltf(sys.argv[2])
joints = [n for n in a.names if n and (n.startswith('B_') or n.startswith('Serpent') or n in ('Root', 'Polearm'))]
for clip in [x['name'] for x in a.doc['animations']]:
    A, Bn = a.animation(clip), b.animation(clip); d = a.duration(clip); worst = 0; tip = 0
    for f in range(int(round(d * 48)) + 1):
        t = min(f / 48, d); ga, gb = a.globals(A, t), b.globals(Bn, t)
        for n in joints:
            worst = max(worst, np.linalg.norm(ga[a.names[n]][:3, 3] - gb[b.names[n]][:3, 3]))
        pa, pb = ga[a.names['Polearm']] @ [0, 1.2, 0, 1], gb[b.names['Polearm']] @ [0, 1.2, 0, 1]; tip = max(tip, np.linalg.norm(pa - pb))
    print(f'{clip:9s} joints max {worst * 1000:8.3f} mm  polearm tip {tip * 1000:8.3f} mm')
