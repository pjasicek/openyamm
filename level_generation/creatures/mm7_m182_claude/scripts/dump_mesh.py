"""Dump a blend's Body mesh (rest coordinates, triangles, part attribute, and vertex groups if any) to an npz for
system-Python analysis. Usage: blender -b --python dump_mesh.py -- <in.blend> <out.npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); o = bpy.data.objects['Body']; me = o.data
rig = bpy.data.objects.get('Rig')
if rig is not None:
    rig.animation_data_clear() if rig.animation_data else None
    for pb in rig.pose.bones: pb.matrix_basis.identity()
co = np.array([v.co[:] for v in me.vertices]); me.calc_loop_triangles()
tris = np.array([t.vertices[:] for t in me.loop_triangles]); tri_face = np.array([t.polygon_index for t in me.loop_triangles])
mat = np.array([me.polygons[i].material_index for i in tri_face])
out = {'co': co, 'tris': tris, 'tri_face': tri_face, 'mat': mat}
if 'part' in me.attributes:
    out['part'] = np.array([v.value for v in me.attributes['part'].data])
names = [g.name for g in o.vertex_groups]
if names:
    W = np.zeros((len(co), len(names)), np.float32)
    for v in me.vertices:
        for g in v.groups: W[v.index, g.group] = g.weight
    out['weights'] = W; out['group_names'] = np.array(names)
if rig is not None:
    bn = [b.name for b in rig.data.bones]
    out['bone_names'] = np.array(bn)
    out['bone_rest'] = np.array([np.array(b.matrix_local) for b in rig.data.bones])
    out['bone_parent'] = np.array([bn.index(b.parent.name) if b.parent else -1 for b in rig.data.bones])
    out['bone_head'] = np.array([b.head_local[:] for b in rig.data.bones]); out['bone_tail'] = np.array([b.tail_local[:] for b in rig.data.bones])
for name in ('wing', 'head', 'jaw', 'fore', 'hind'):
    if name in me.attributes and me.attributes[name].domain == 'POINT':
        out[name] = np.array([v.value for v in me.attributes[name].data], bool)
np.savez_compressed(a[1], **out); print('DUMP', {k: np.shape(v) for k, v in out.items()})
