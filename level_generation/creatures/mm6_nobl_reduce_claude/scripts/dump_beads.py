"""Centres of the small Meshy 'chain link' pieces (6-vertex octahedra) of the installed source mesh in rest pose ->
work/beads.npy (x, y, z per piece), plus the clasp pieces' vertices -> work/clasp.npz. Usage: blender -b -P dump_beads.py"""
import os, bpy, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_facecape.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
o = bpy.data.objects['Body']; mw = o.matrix_world
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen, beads, clasp = set(), [], []
for v in bm.verts:
    if v.index in seen:
        continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); stack.append(y)
    pts = np.array([(mw @ x.co)[:] for x in comp])
    if len(comp) == 6 and 1.15 < pts[:, 2].mean() < 1.45:
        beads.append(pts.mean(0))
    elif len(comp) in (33, 34, 48) and pts[:, 1].mean() < -.12:
        clasp.append(pts)
np.save(os.path.join(HERE, 'work', 'beads.npy'), np.array(beads))
np.savez(os.path.join(HERE, 'work', 'clasp.npz'), *clasp)
print('BEADS', len(beads), 'CLASP pieces', [len(c) for c in clasp], [c.mean(0).round(3).tolist() for c in clasp])
