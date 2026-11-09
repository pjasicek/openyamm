"""hgd G1: clay frames of candidate clips on our rig with a stand-in rifle on the right hand (barrel along the hand's
+Y from 0.25 m behind the wrist to 0.75 m ahead, 6 cm toward the hand's +Z), so the hold reads. Frames to
<out dir>/<clip>_<i>_<view>.png and rows.json. Args: -- <blend> <out dir> <frames> <views> clip [...]"""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out, n, views, clips = a[1], int(a[2]), a[3].split(','), a[4:]
os.makedirs(out, exist_ok=True)
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; common.workbench_clay(sc)
OFF = [float(x) for x in os.environ.get('ROD_OFF', '0,0,0.06').split(',')]
bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=1.0, vertices=12)
rod = bpy.context.active_object
rod.parent = rig; rod.parent_type = 'BONE'; rod.parent_bone = 'B_R_Hand'
# bone-parented objects sit at the bone TAIL; local frame = bone frame (Y along the bone)
tail_len = rig.data.bones['B_R_Hand'].length
rod.matrix_parent_inverse = Matrix.Identity(4)
rod.location = Vector((OFF[0], 0.25 - tail_len + OFF[1], OFF[2]))
rod.rotation_euler = (1.5708, 0, 0)
rows = []
for c in clips:
    act = bpy.data.actions[c]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; row = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(n - 1, 1); sc.frame_set(int(f), subframe=f - int(f))
        row.append(common.render_views(os.path.join(out, f'{c}_{i}'), 0.95, 2.3, views=tuple(views), resolution=(220, 300)))
    rows.append((c, row))
json.dump(rows, open(os.path.join(out, 'rows.json'), 'w'))
