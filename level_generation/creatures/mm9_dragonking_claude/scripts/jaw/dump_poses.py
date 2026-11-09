"""Dump pose-bone matrix_basis of role clips at given times from an animated blend (bone names = MM9 names).
Args: -- <anim blend> <out json> Clip@seconds ..."""
import bpy, sys, json, math
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
out = {}
for spec in a[2:]:
    clip, t = spec.split('@'); t = float(t)
    rig.animation_data.action = bpy.data.actions[clip]
    f = t * 30; sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    out[spec] = {pb.name: [list(r) for r in pb.matrix_basis] for pb in rig.pose.bones}
json.dump(out, open(a[1], 'w'))
print('POSES', list(out))
