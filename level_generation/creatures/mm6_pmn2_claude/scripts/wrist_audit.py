"""Wrist audit: Hand bone local rotation relative to rest, split into swing (bend) and twist about the forearm axis,
per frame of each clip; also forearm twist relative to the upper arm. Args: blend [actions...]."""
import bpy, sys, os, math
from mathutils import Quaternion, Vector
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args[0]))
arm = bpy.data.objects['Mage_Rig']; scene = bpy.context.scene


def swing_twist(q, axis=Vector((0, 1, 0))):
    p = Vector((q.x, q.y, q.z)).project(axis)
    t = Quaternion((q.w, p.x, p.y, p.z)); t.normalize()
    s = q @ t.inverted()
    tw = math.degrees(2 * math.atan2(p.length, q.w)) * (1 if p.dot(axis) >= 0 else -1)
    return math.degrees(s.angle), (tw + 180) % 360 - 180


names = args[1:] or [a.name for a in bpy.data.actions if not a.name.endswith('_src')]
for name in names:
    act = bpy.data.actions[name]; arm.animation_data.action = act
    if getattr(act, 'slots', None): arm.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    st = {}
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        for side in ('Left', 'Right'):
            for bone in ('Hand', 'ForeArm'):
                pb = arm.pose.bones[f'mixamorig:{side}{bone}']
                parent = pb.parent
                # rotation of the bone relative to its parent, compared with rest
                rel = (parent.matrix.inverted() @ pb.matrix).to_quaternion()
                rest = (parent.bone.matrix_local.inverted() @ pb.bone.matrix_local).to_quaternion()
                q = rest.inverted() @ rel
                sw, tw = swing_twist(q)
                st.setdefault((side, bone), []).append((sw, tw))
    for (side, bone), v in sorted(st.items()):
        sw = [a for a, b in v]; tw = [b for a, b in v]
        print(f'WRIST {name:8s} {side:5s} {bone:7s} swing max {max(sw):6.1f} mean {sum(sw)/len(sw):6.1f}   twist min {min(tw):7.1f} max {max(tw):7.1f}')
