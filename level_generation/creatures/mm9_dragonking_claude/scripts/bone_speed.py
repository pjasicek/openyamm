"""Per-frame world speed of a bone tail in an action (model units/s). Args: blend action bone [bone2]"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions[argv[1]]; arm.animation_data.action = act
sc = bpy.context.scene; fps = sc.render.fps
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
prev = None; out = []
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    p = [arm.matrix_world @ arm.pose.bones[b].tail for b in argv[2:]]
    if prev:
        out.append((f, round(max((a - b).length for a, b in zip(p, prev)) * fps, 2), round(p[0].y, 2), round(p[0].z, 2)))
    prev = p
print('SPEED', out)
