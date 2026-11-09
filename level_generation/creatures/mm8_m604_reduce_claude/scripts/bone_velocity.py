#!/usr/bin/env python3
"""Per-bone local angular velocity (deg/s) of a clip from a GLB's animation data (rotation channels, glTF key
times), plus pelvis translation speed (m/s). Prints the bones with the largest peak over a window and writes
work/vel_<label>.npz (times, names, deg/s per bone). Usage: bone_velocity.py <glb> <label> [t0 t1] [clip]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
glb, label = sys.argv[1:3]; t0, t1 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0, 9)
clip = sys.argv[5] if len(sys.argv) > 5 else 'Attack'
d, b = read_glb(Path(glb)); an = next(a for a in d['animations'] if a['name'] == clip)
names, vel, times = [], [], None
for ch in an['channels']:
    s = an['samplers'][ch['sampler']]
    t = np.frombuffer(accessor_bytes(d, b, s['input']), np.float32)
    if len(t) < 3:
        continue
    times = t
    n = d['nodes'][ch['target']['node']]['name']
    if ch['target']['path'] == 'rotation':
        q = np.frombuffer(accessor_bytes(d, b, s['output']), np.float32).reshape(-1, 4)
        dot = np.abs((q[1:] * q[:-1]).sum(1)).clip(0, 1); w = np.degrees(2 * np.arccos(dot)) / np.diff(t)
        names.append(n); vel.append(np.r_[0, w])
    elif ch['target']['path'] == 'translation' and n == 'B_Pelvis':
        p = np.frombuffer(accessor_bytes(d, b, s['output']), np.float32).reshape(-1, 3)
        names.append('B_Pelvis[m/s x100]'); vel.append(np.r_[0, np.linalg.norm(np.diff(p, axis=0), axis=1) / np.diff(t) * 100])
vel = np.array(vel); np.savez(Path(__file__).resolve().parents[1] / 'work' / f'vel_{label}.npz', t=times, names=np.array(names), vel=vel)
m = (times >= t0) & (times <= t1)
order = np.argsort(-vel[:, m].max(1))
for i in order[:14]:
    k = np.argmax(vel[i] * m)
    print(f'{label} {names[i]:22s} peak {vel[i, k]:7.0f} at {times[k]:.3f}s')
