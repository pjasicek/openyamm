"""Per-frame world positions of bone heads (and the claw tip: hand head + 0.45 m along the hand's +Y) for clip choice
and impact timing. Args: -- <blend> <action> <bone,bone,...> [step]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
blend, act, bones = a[0], a[1], a[2].split(','); step = int(a[3]) if len(a) > 3 else 2
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; A = bpy.data.actions[act]
rig.animation_data_create(); rig.animation_data.action = A
if len(A.slots): rig.animation_data.action_slot = A.slots[0]
f0, f1 = map(int, A.frame_range)
for f in range(f0, f1 + 1, step):
    bpy.context.scene.frame_set(f)
    out = []
    for b in bones:
        pb = rig.pose.bones[b]; p = rig.matrix_world @ pb.head
        out.append(f'{b[2:]}({p.x:+.2f},{p.y:+.2f},{p.z:+.2f})')
    print(f'PROBE {act} f{f:3d} t{f/30:.2f} ' + ' '.join(out))
