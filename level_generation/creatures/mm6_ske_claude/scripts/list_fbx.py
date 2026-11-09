"""List Mixamo FBX clips: duration at 24 fps scene rate, hips travel. Args: -- <dir>"""
import bpy, sys, os, glob
d = sys.argv[sys.argv.index('--') + 1]
for f in sorted(glob.glob(os.path.join(d, '*.fbx'))):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    sc = bpy.context.scene
    arm = next((o for o in sc.objects if o.type == 'ARMATURE'), None)
    act = arm.animation_data.action if arm and arm.animation_data else None
    if not act:
        print(f'CLIP\t{os.path.basename(f)}\tno action'); continue
    f0, f1 = act.frame_range
    fps = sc.render.fps / sc.render.fps_base
    hips = arm.pose.bones.get('mixamorig:Hips')
    pts = []
    for fr in (int(f0), int(f1)):
        sc.frame_set(fr); pts.append((arm.matrix_world @ hips.head).copy())
    tr = pts[1] - pts[0]
    print(f'CLIP\t{os.path.basename(f)}\t{(f1 - f0) / fps:.2f}s\tfps {fps:.0f}\tframes {f1 - f0:.0f}\t'
          f'travel x{tr.x:+.2f} y{tr.y:+.2f} z{tr.z:+.2f}')
