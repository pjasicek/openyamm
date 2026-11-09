"""Jaw opening per clip: angle of Xjaw (and Xtong) relative to Xjawbase vs the bind pose, sampled at 30 fps.
Args: -- <anim blend> [out json]"""
import bpy, sys, json, math
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
def rel(name, base='Xjawbase'):
    pb, pa = rig.pose.bones[name], rig.pose.bones[base]
    return pa.matrix.inverted() @ pb.matrix
for b in rig.pose.bones:
    b.matrix_basis.identity()
rig.animation_data_create(); rig.animation_data.action = None
bpy.context.view_layer.update()
bind = rel('Xjaw').to_quaternion()
out = {}
for act in bpy.data.actions:
    rig.animation_data.action = act
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    angs = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        q = rel('Xjaw').to_quaternion()
        d = bind.rotation_difference(q)
        ang = math.degrees(d.angle)
        # sign: opening = jaw tip moves down (relative tail z in Xjawbase space)
        tip = (rel('Xjaw') @ rig.pose.bones['Xjaw'].bone.matrix_local.inverted() @ rig.pose.bones['Xjaw'].bone.tail_local)
        angs.append((f, round(ang, 1)))
    mx = max(angs, key=lambda x: x[1]); mn = min(angs, key=lambda x: x[1])
    out[act.name] = {'frames': [f0, f1], 'max_deg': mx[1], 'max_frame': mx[0], 'max_s': round(mx[0] / 30, 3),
                     'min_deg': mn[1], 'min_s': round(mn[0] / 30, 3),
                     'open_over_20': [round(f / 30, 2) for f, x in angs if x > 20][:1] + [round(f / 30, 2) for f, x in angs if x > 20][-1:],
                     'curve': [x for _, x in angs][::3]}
    print(act.name, {k: v for k, v in out[act.name].items() if k != 'curve'})
if len(a) > 1:
    json.dump(out, open(a[1], 'w'), indent=1)
