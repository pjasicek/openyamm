"""G1 probe: per-frame hand positions (relative to hips, metres scaled to a 1.8 m figure) of skin-less Mixamo clips.
Args: -- <fbx> [<fbx> ...]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
for fbx in a:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
    src = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
    pre = next(b.name for b in src.data.bones if b.name.endswith('Hips'))[:-4]
    f0, f1 = map(int, src.animation_data.action.frame_range)
    sc = bpy.context.scene
    sc.frame_set(f0)
    h = (src.matrix_world @ src.pose.bones[pre + 'Head'].head).z
    k = 1.6 / h
    print('CLIP', os.path.basename(fbx), f0, f1, 'fps', sc.render.fps, 'headz', round(h, 3))
    for f in range(f0, f1 + 1, 3):
        sc.frame_set(f)
        P = lambda b: src.matrix_world @ src.pose.bones[pre + b].head
        hip = P('Hips'); L = (P('LeftHand') - hip) * k; R = (P('RightHand') - hip) * k
        print('F %4d hipz %.2f  L %+.2f %+.2f %+.2f  R %+.2f %+.2f %+.2f  sep %.2f' % (f, hip.z * k, *L, *R, (L - R).length))
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o, do_unlink=True)
