"""Step 1 cleanup of the Druidess Smart Topology return (work/st_v1_parts.blend, loose parts P00..; examine_parts.py).
Parts: P00 torso skin + upper arms + forearm skin + the CLOAK (one shell, the cloak joined at the shoulder tops),
P01 hair, P02 legs, P03 hood (closed), P04/P05 hands, P06/P07 boots, P08 belt, P09/P10 bracers, P11 front panel,
P14 belt medallion; P12/P13 eye balls, P15-P17 lash and lip strips, P18+ tiny stud beads.
- the eye balls and lash/lip strips are removed (eyes are painted by the head retexture);
- the stud beads (<= 12 vertices each) are removed (the texture carries the studs);
- the cloak inside P00 gets its own piece id CLOAK_PIECE: flood fill through P00's edges from the hem, limited to
  z < CLOAK_ZC (cloak_split_probe.py: the cloak joins the torso only between z 1.40 and 1.42, at the shoulder tops).
Joins the rest into 'Body' with a 'piece' point attribute (part index; cloak CLOAK_PIECE) and 'orig_co'.
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
from collections import deque
src, out = sys.argv[sys.argv.index('--') + 1:]
CLOAK_PIECE = 100
CLOAK_ZC = 1.40
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
DROP = {'P12', 'P13', 'P15', 'P16', 'P17'} | {n for n, o in P.items() if len(o.data.vertices) <= 12}
for n in sorted(DROP):
    bpy.data.objects.remove(P.pop(n), do_unlink=True)
print('DROPPED', len(DROP), sorted(DROP))
for n, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
# cloak label inside P00
p0 = P['P00']; me0 = p0.data
co = np.array([tuple(p0.matrix_world @ v.co) for v in me0.vertices])
nbr = [[] for _ in co]
for e in me0.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
seed = [i for i in range(len(co)) if co[i, 2] < 0.2]
seen = set(seed); q = deque(seed)
while q:
    i = q.popleft()
    for j in nbr[i]:
        if j not in seen and co[j, 2] < CLOAK_ZC:
            seen.add(j); q.append(j)
pv = np.zeros(len(co), np.int32)
pv[sorted(seen)] = CLOAK_PIECE
me0.attributes['piece'].data.foreach_set('value', pv)
print('CLOAK verts', len(seen), 'of', len(co))
for o in bpy.data.objects:
    o.select_set(o.name in P)
bpy.context.view_layer.objects.active = p0
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
body.data.materials.clear()
print('TRIS', sum(len(p.vertices) - 2 for p in body.data.polygons))
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
