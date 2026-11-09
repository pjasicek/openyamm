#!/usr/bin/env python3
"""Body faces the head and jaw touch in motion (a55 gates: head and jaw into the torso rose a little in Fidget2, AttackMelee2,
Taunt, Death: the chest under the jaw had larger triangles): body faces with a corner within D m of a head-primitive vertex in
any pose (every clip at 10 Hz, installed GLB). Writes work/keep_extra_headc.npy (per body face of Trog_A). Usage: head_contact.py [D]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
import bglbio as gb  # noqa: E402
D = float(sys.argv[1]) if len(sys.argv) > 1 else 0.03
src = HERE / 'before' / 'mm9_troglodyte.glb'
doc, b = gb.read(src); node = next(n for n in doc['nodes'] if n.get('name') == 'Troglodyte' and 'mesh' in n)
T = gb.prims(doc, b, node['mesh'])[0]['T']
m = Model(Glb(str(src))); hit = np.zeros(len(T), bool); poses = 0
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 0.1), t1):
        sp = m.skinned_positions(m.world(m.sample(clip, t))); body, head = sp[0][0], sp[1][0]
        near = cKDTree(head).query(body, distance_upper_bound=D)[0] < D
        hit |= near[T].any(1); poses += 1
np.save(HERE / 'work' / 'keep_extra_headc.npy', hit); print('HEAD CONTACT', D, 'poses', poses, 'body faces', int(hit.sum()))
