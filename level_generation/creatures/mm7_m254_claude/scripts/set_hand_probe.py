"""G1 probe: per-frame hand/pelvis heights and forward reach of humanoid-set clips (character turned to face -Y,
heights scaled to a 1.8 m head-top figure). Args: -- <set glb> clip [clip ...]"""
import bpy, sys, os, math
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(a[0]))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.rotation_mode = 'XYZ'; arm.rotation_euler = (0, 0, math.pi)
sc = bpy.context.scene
for clip in a[1:]:
    act = next(x for x in bpy.data.actions if x.name.replace('RPG-Character|', '').replace('-', '').replace('_', '').lower().startswith(clip.lower().replace('-', '')))
    arm.animation_data.action = act
    f0, f1 = map(int, act.frame_range)
    P = lambda b: arm.matrix_world @ arm.pose.bones[b].head
    sc.frame_set(f0); hz = P('B_Head').z; k = 1.6 / hz
    print('CLIP', act.name, f0, f1, 'fps', sc.render.fps)
    for f in range(f0, f1 + 1, 2):
        sc.frame_set(f)
        pel = P('B_Pelvis'); L = P('B_L_Hand'); R = P('B_R_Hand')
        print('F %3d pelz %.2f  L z %.2f fwd %+.2f x %+.2f  R z %.2f fwd %+.2f x %+.2f  sep %.2f headz %.2f' % (
            f, pel.z * k, L.z * k, -(L.y - pel.y) * k, L.x * k, R.z * k, -(R.y - pel.y) * k, R.x * k, (L - R).length * k, P('B_Head').z * k))
