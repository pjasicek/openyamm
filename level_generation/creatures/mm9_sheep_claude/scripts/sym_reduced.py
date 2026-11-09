"""Make the reduced, weighted 'Body' exactly mirror-symmetric (decimation broke it): Blender Symmetrize keeps +X, and
every mirrored vertex swaps its L/R groups (Xfoo01, the +X bone, <-> Xfoo, the -X bone). Eyes, ears and the slit
follow. Args: <in blend> <out blend>"""
import bpy, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
o = bpy.data.objects['Body']
for x in bpy.data.objects:
    x.select_set(x == o)
bpy.context.view_layer.objects.active = o
n0 = len(o.data.vertices)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.symmetrize(direction='POSITIVE_X', threshold=0.0003)
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')
me = o.data
for g in [g.name for g in o.vertex_groups]:
    if g.endswith('01') and g[:-2] not in o.vertex_groups:
        o.vertex_groups.new(name=g[:-2])
    if not g.endswith('01') and g + '01' in bpy.data.objects['MM9_Rig'].data.bones and g + '01' not in o.vertex_groups:
        o.vertex_groups.new(name=g + '01')
name = {g.index: g.name for g in o.vertex_groups}
idx = {g.name: g.index for g in o.vertex_groups}
swap = {}
for g, i in idx.items():
    if g.endswith('01') and g[:-2] in idx:
        swap[i] = idx[g[:-2]]; swap[idx[g[:-2]]] = i
n_sw = 0
for v in me.vertices:
    if v.co.x >= -1e-4:
        continue
    w = {g.group: g.weight for g in v.groups}
    if not any(k in swap for k in w):
        continue
    for k in w:
        o.vertex_groups[name[k]].remove([v.index])
    for k, wt in w.items():
        o.vertex_groups[name[swap.get(k, k)]].add([v.index], wt, 'REPLACE')
    n_sw += 1
P = np.array([tuple(v.co) for v in me.vertices])
print('SYMR ' + json.dumps({'before': n0, 'verts': len(P), 'tris': len(me.polygons), 'swapped': n_sw}))
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
