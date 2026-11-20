"""Connected pieces of the reduced candidate (work/ladder.blend, REA_CAND) for the horn/spike rebuild: per face its
piece id, material slot, UV centroid, centre; per vertex the dominant bone. Out: work/pieces.npz.
Usage: blender -b -P dump_pieces.py"""
import os
import bmesh
import bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
o = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_55')]; rig = bpy.data.objects['Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
uvl = bm.loops.layers.uv.active
comp = np.full(len(bm.verts), -1); n = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    stack = [v]; comp[v.index] = n
    while stack:
        x = stack.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = n; stack.append(y)
    n += 1
names = [g.name for g in o.vertex_groups]
dom = np.array([max(v.groups, key=lambda e: e.weight).group if len(v.groups) else -1 for v in o.data.vertices])
fpiece = np.array([comp[f.verts[0].index] for f in bm.faces])
fmat = np.array([f.material_index for f in bm.faces])
fuv = np.array([np.mean([l[uvl].uv[:] for l in f.loops], 0) for f in bm.faces])
fc = np.array([f.calc_center_median()[:] for f in bm.faces])
co = np.array([v.co[:] for v in bm.verts])
np.save(os.path.join(HERE, "work", "face_verts.npy"), np.array([[v.index for v in f.verts] for f in bm.faces], dtype=object), allow_pickle=True)
np.savez(os.path.join(HERE, 'work', 'pieces.npz'), fpiece=fpiece, fmat=fmat, fuv=fuv, fc=fc, co=co, vpiece=comp,
         dom=dom, bones=np.array(names), mats=np.array([m.name for m in o.data.materials]))
print('PIECES', n, 'faces', len(fpiece))
