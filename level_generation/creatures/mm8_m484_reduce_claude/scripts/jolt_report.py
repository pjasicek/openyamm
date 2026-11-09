#!/usr/bin/env python3
"""Per-bone local angular speed of a clip (deg/s, from the GLB keys) and the largest change of speed from one viewer
frame (1/48 s) to the next, overall and before the impact. Usage: jolt_report.py <glb> [clip]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
glb = sys.argv[1]; clip = sys.argv[2] if len(sys.argv) > 2 else 'Attack'
d, b = read_glb(Path(glb)); an = next(a for a in d['animations'] if a['name'] == clip)
names, vel, times = [], [], None
for ch in an['channels']:
    s = an['samplers'][ch['sampler']]
    t = np.frombuffer(accessor_bytes(d, b, s['input']), np.float32)
    if ch['target']['path'] != 'rotation' or len(t) < 3:
        continue
    q = np.frombuffer(accessor_bytes(d, b, s['output']), np.float32).reshape(-1, 4)
    w = np.degrees(2 * np.arccos(np.abs((q[1:] * q[:-1]).sum(1)).clip(0, 1))) / np.diff(t)
    names.append(d['nodes'][ch['target']['node']]['name']); vel.append(np.r_[w[0], w]); times = t
vel = np.array(vel); fr = np.searchsorted(times, np.arange(0, times[-1], 1 / 48)); jv = np.abs(np.diff(vel[:, fr], axis=1))
i, j = np.unravel_index(jv.argmax(), jv.shape)
print(f'{clip}: peak {vel.max():.0f} deg/s ({names[int(vel.max(1).argmax())]}); largest change per viewer frame '
      f'{jv.max():.0f} deg/s ({names[i]} at {times[fr[j]]:.3f} s)')
m = times[fr[:-1]] < 0.78
if m.any():
    jj = np.unravel_index(jv[:, m].argmax(), jv[:, m].shape)
    print(f'  before the downswing (< 0.78 s): {jv[:, m].max():.0f} deg/s ({names[jj[0]]} at {times[fr[:-1]][m][jj[1]]:.3f} s)')
order = np.argsort(-jv.max(1))[:5]
print('  largest changes per bone:', ', '.join(f'{names[k]} {jv[k].max():.0f}' for k in order))
still = vel.max(0) < 20
print('  still keys (< 20 deg/s every bone):', [round(float(x), 3) for x in times[still]][:12])
for n in ('Axe', 'B_R_Forearm', 'B_R_UpperArm', 'B_L_UpperArm', 'B_Head'):
    if n in names:
        v = vel[names.index(n)]; print(f'  {n:13s}', ' '.join(f'{x:4.0f}' for x in v[(times > 0.5) & (times < 0.76)]))
