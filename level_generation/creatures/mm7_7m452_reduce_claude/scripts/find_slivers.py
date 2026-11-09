"""Probe: sliver faces of the Body (longest edge > MINLEN and altitude over it < MAXALT), with their shell, centre and the
angle between their normal and the neighbouring faces' (a spike stands off the surface). Args: -- <blend>
(env MINLEN=0.025 MAXALT=0.004)"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
me = bpy.data.objects['Body'].data
MINLEN, MAXALT = float(os.environ.get('MINLEN', '0.025')), float(os.environ.get('MAXALT', '0.004'))
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in me.vertices])
vf = {}
for p in me.polygons:
    for v in p.vertices:
        vf.setdefault(v, []).append(p.index)
out = []
for p in me.polygons:
    P = co[list(p.vertices)]
    e = [np.linalg.norm(P[(i + 1) % len(P)] - P[i]) for i in range(len(P))]
    L = max(e); alt = 2 * p.area / L if L > 0 else 0
    if L > MINLEN and alt < MAXALT:
        nb = {f for v in p.vertices for f in vf[v]} - {p.index}
        dev = max((np.degrees(np.arccos(np.clip(np.dot(p.normal, me.polygons[f].normal), -1, 1))) for f in nb), default=0)
        out.append((L, alt, p.index, pv[p.vertices[0]], P.mean(0), dev, len(p.vertices)))
for L, alt, i, pc, c, dev, n in sorted(out, key=lambda x: -x[0])[:40]:
    print(f'SLIVER face {i} ({n}v) piece {pc} long {L * 100:.1f} cm alt {alt * 1000:.1f} mm centre {np.round(c, 3)} max normal dev {dev:.0f}')
print('SLIVER total', len(out))
