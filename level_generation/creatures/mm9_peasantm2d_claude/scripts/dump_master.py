"""Dump the master's Body mesh (rest pose): vertex positions, faces, face attributes, UV layers, Head bone weight, joints. Args: <blend> <out npz>"""
import bpy, sys, numpy as np, json
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
P = np.array([body.matrix_world @ v.co for v in me.vertices])
F = np.array([p.vertices[:] for p in me.polygons])
att = {}
for a in me.attributes:
    if a.domain == 'FACE' and a.data_type == 'INT':
        x = np.zeros(len(me.polygons), np.int32); a.data.foreach_get('value', x); att['f_' + a.name] = x
uvs = {}
for l in me.uv_layers:
    x = np.zeros(len(me.loops) * 2, np.float32); l.data.foreach_get('uv', x); uvs['uv_' + l.name] = x.reshape(-1, 2)
gi = body.vertex_groups['Bip01 Head'].index
hw = np.array([next((g.weight for g in v.groups if g.group == gi), 0.0) for v in me.vertices])
J = {b.name: list(rig.matrix_world @ b.head_local) for b in rig.data.bones}
print('DUMP', len(P), len(F), list(att), list(uvs), 'mw', [list(r) for r in body.matrix_world], 'rig', [list(r) for r in rig.matrix_world])
print('DUMP groups', len(body.vertex_groups), 'objects', [o.name for o in bpy.data.objects])
np.savez(OUT, P=P, F=F, hw=hw, J=json.dumps(J), **att, **uvs)
