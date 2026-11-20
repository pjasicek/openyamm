"""Scale the wings to the native proportions, in place on the textured master (work/rig_v6.blend), after the clips are
synced: the native sprites span about 1.2 x the figure height (m150sa0 211 px wide over 179 px tall; the back view sa4
215 px), the HD masters' wings 1.55 x. Each wing's vertices (garment 5) and its Wing_<s>_1..3 bones move toward the
wing root (Wing_<s>_1 head) by WING_SCALE, fading in over |x| 0.06..0.16 m so the coverts strap across the back stays
put. Geometry and bones move together, so weights, UVs and the rotation-only wing clips stay valid.
Args: -- <blend>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
K = float(os.environ.get('WING_SCALE', '0.78'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
if rig.get('wing_scale_applied'):
    print('WINGSCALE already applied', rig['wing_scale_applied']); raise SystemExit
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
root = {s: rig.data.bones[f'Wing_{s}_1'].head_local.copy() for s in 'LR'}


def move(p):
    s = 'L' if p.x > 0 else 'R'
    t = min(max((abs(p.x) - 0.06) / 0.10, 0.0), 1.0); w = t * t * (3 - 2 * t)
    return root[s] + (p - root[s]) * (1 - w * (1 - K))


gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
inv = body.matrix_world.inverted()
n = 0
for v in me.vertices:
    if gv[v.index] == 5:
        v.co = inv @ move(body.matrix_world @ v.co); n += 1
me.update()
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for s in 'LR':
    for i in (1, 2, 3):
        eb = rig.data.edit_bones[f'Wing_{s}_{i}']
        roll = eb.roll
        eb.head = move(eb.head.copy()); eb.tail = move(eb.tail.copy()); eb.roll = roll
bpy.ops.object.mode_set(mode='OBJECT')
rig['wing_scale_applied'] = K
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
print('WINGSCALE', K, 'vertices', n, 'span m', round(float(np.ptp(co[:, 0])), 3), 'height m', round(float(co[:, 2].max()), 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
