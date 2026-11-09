"""MM9 mouse clip keys: per key time, Bone05 head position and rotation (euler deg, armature space) and Bone08/Bone01
rotations relative to their rest. Args: <rig blend> <action>"""
import bpy, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = bpy.data.objects['MM9_Rig']
sc = bpy.context.scene
act = bpy.data.actions[argv[1]]
arm.animation_data.action = act
try:
    arm.animation_data.action_slot = act.slots[0]
except Exception:
    pass
f0, f1 = act.frame_range
n = int(argv[2]) if len(argv) > 2 else 12
for k in range(n + 1):
    f = f0 + (f1 - f0) * k / n
    sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    out = []
    for b in ('Bone05', 'Bone08', 'Bone06', 'Bone01', 'Bone02'):
        pb = arm.pose.bones[b]
        m = pb.matrix @ pb.bone.matrix_local.inverted()
        e = m.to_euler()
        out.append('%s p(%.4f %.4f %.4f) r(%.1f %.1f %.1f)' % (b, *pb.head, *(math.degrees(x) for x in e)))
    print('KEY t=%.3f ' % ((f - f0) / sc.render.fps) + ' | '.join(out))
