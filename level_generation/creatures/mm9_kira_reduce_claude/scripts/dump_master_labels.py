"""Kira's final master (mm9_kira_claude/work/uv_v6.blend, the mesh the installed r8 GLB was exported from): per-face labels
(every int/bool face attribute: part, hand, ...) with the face centroid in world space and the material, for mapping onto the
installed GLB's triangles (label_faces.py). Usage: blender -b -P dump_master_labels.py -- <blend> <out npz>"""
import bpy, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']; me = ob.data
print('OBJECTS', [(o.name, o.type) for o in bpy.data.objects])
print('ATTRS', [(a.name, a.domain, a.data_type) for a in me.attributes if not a.name.startswith('.')])
print('UV', [u.name for u in me.uv_layers], 'MATS', [m.name if m else None for m in me.materials])
mw = ob.matrix_world
out = {'cen': np.array([tuple(mw @ p.center) for p in me.polygons], np.float32),
       'mat': np.array([p.material_index for p in me.polygons], np.int32),
       'nv': np.array([len(p.vertices) for p in me.polygons], np.int32)}
for a in me.attributes:
    if a.domain == 'FACE' and a.data_type in ('INT', 'BOOLEAN', 'INT8') and not a.name.startswith('.'):
        v = np.zeros(len(me.polygons), np.int32 if a.data_type != 'BOOLEAN' else bool); a.data.foreach_get('value', v)
        out['f_' + a.name] = v.astype(np.int32)
        u, c = np.unique(v, return_counts=True); print('FACEATTR', a.name, dict(zip(u.tolist(), c.tolist())))
print('MATRIX', [list(r) for r in mw])
print('TRIS', int((out['nv'] - 2).sum()), 'polys', len(me.polygons))
np.savez(OUT, **out)
