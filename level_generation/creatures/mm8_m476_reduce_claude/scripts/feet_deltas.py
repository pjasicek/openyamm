#!/usr/bin/env python3
"""Leg rotation changes between two GLBs: per clip and leg bone, the largest change of the local rotation and the
largest frame-to-frame rotation step before -> after (a jerk shows as a step far above the source's own).
Usage: feet_deltas.py <before.glb> <after.glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
LEG = ('B_L_Thigh', 'B_L_Calf', 'B_L_Foot', 'B_R_Thigh', 'B_R_Calf', 'B_R_Foot')


def chans(p):
    d, b = read_glb(Path(p)); names = [n.get('name') for n in d['nodes']]; out = {}
    for a in d['animations']:
        for c in a['channels']:
            if c['target']['path'] == 'rotation' and names[c['target']['node']] in LEG:
                s = a['samplers'][c['sampler']]
                out[(a['name'], names[c['target']['node']])] = (np.frombuffer(accessor_bytes(d, b, s['input']), np.float32),
                                                                 np.frombuffer(accessor_bytes(d, b, s['output']), np.float32).reshape(-1, 4))
    return out


A, B = chans(sys.argv[1]), chans(sys.argv[2])
ang = lambda a, b: np.degrees(2 * np.arccos(np.clip(np.abs((a * b).sum(-1)), 0, 1)))
for clip in sorted({c for c, _ in B}):
    row, changed = [], False
    for bone in LEG:
        tb, qb = B[(clip, bone)]; ta, qa0 = A[(clip, bone)]
        qa = qa0[np.clip(np.searchsorted(ta, tb, 'right') - 1, 0, len(ta) - 1)]
        d = ang(qa, qb); changed |= d.max() > 1e-3
        row.append(f"{bone[2:]} d{d.max():.1f} step {ang(qa[1:], qa[:-1]).max():.1f}->{ang(qb[1:], qb[:-1]).max():.1f}")
    print(f'{clip:9s}', ' | '.join(row) if changed else 'unchanged')
