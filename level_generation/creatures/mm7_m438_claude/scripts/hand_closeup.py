"""Clay close-ups around a bone at action frames (front, left, right, back views). Args: -- <blend> <bone> <out prefix>
<scale m> action:frame [...]"""
import bpy, sys, os, json
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, bone, out, scale, picks = a[0], a[1], a[2], float(a[3]), a[4:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene; common.workbench_clay(scene)
rows = []
for pk in picks:
    an, f = pk.split(':'); act = bpy.data.actions[an]
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    scene.frame_set(int(f))
    c = (rig.matrix_world @ rig.pose.bones[bone].matrix).translation
    row = []
    for v in ('front', 'left', 'right', 'back'):
        p = common.render_views(f'{out}_{an}{f}', c.z, scale, views=(v,), resolution=(320, 320), target=(c.x, c.y))[0]
        row.append([p, f'{an} {f} {v}'])
    rows.append(row)
d = os.path.dirname(out); json.dump(rows, open(os.path.join(d, 'frames.json'), 'w'))
