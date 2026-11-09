"""Probe: faces of a shell whose longest edge is RATIO x the median edge of the surrounding faces (a triangle bridging
two surfaces), with their centre, vertex pieces and the far vertex. Args: -- <blend>   (env PIECES=0 RATIO=3)"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
me = bpy.data.objects['Body'].data
PIECES = {int(x) for x in os.environ.get('PIECES', '0').split(',')}; RATIO = float(os.environ.get('RATIO', '3'))
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in me.vertices])
el = {}
for e in me.edges:
    i, j = e.vertices; L = np.linalg.norm(co[i] - co[j]); el.setdefault(i, []).append(L); el.setdefault(j, []).append(L)
rows = []
for p in me.polygons:
    if pv[p.vertices[0]] not in PIECES:
        continue
    P = co[list(p.vertices)]; L = max(np.linalg.norm(P[(k + 1) % len(P)] - P[k]) for k in range(len(P)))
    ring = np.median([x for v in p.vertices for x in el[v]])
    if L > RATIO * ring and L > 0.03:
        rows.append((L / ring, L, p.index, P.mean(0), list(p.vertices)))
for r, L, i, c, vs in sorted(rows, key=lambda x: -x[0])[:25]:
    print(f'LONGFACE {i} ratio {r:.1f} long {L * 100:.1f} cm centre {np.round(c, 3)} verts {vs}')
