"""Boundary edges of a ladder candidate that have no boundary edge of the source within 1 mm (rest pose): where a
candidate's extra open edge sits. Usage: blender -b -P open_diff.py -- <ladder blend> <Cand_NN>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
def bnd(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    m = np.array([tuple((e.verts[0].co + e.verts[1].co) / 2) for e in bm.edges if e.is_boundary]); bm.free(); return m
S = bnd(bpy.data.objects['Body']); C = bnd(bpy.data.objects[a[1]])
d = np.array([np.min(np.linalg.norm(S - c, axis=1)) for c in C])
print('OPENDIFF source', len(S), 'cand', len(C), 'cand edges without a source edge within 1 mm:', [tuple(np.round(C[i], 3)) for i in np.where(d > 0.001)[0]])
