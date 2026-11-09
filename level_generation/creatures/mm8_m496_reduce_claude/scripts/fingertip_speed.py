"""Per-frame fingertip speed of Fidget and Hit at the viewer's 48 frames per second, straight from GLBs: world
displacement of the LeftHandMiddle3 and RightHandMiddle3 bone tails per frame (mm). Usage: blender -b -P
fingertip_speed.py -- <label=glb,...>  -> work/fingertips.json"""
import bpy, json, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = {}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    fps = sc.render.fps / sc.render.fps_base
    for clip in ('Fidget', 'Hit'):
        act = next(a for a in bpy.data.actions if a.name.split('_')[0] == clip or a.name == clip)
        rig.animation_data.action = act; f0, f1 = act.frame_range; n = int(round((f1 - f0) / fps * 48)) + 1
        pts = {b: [] for b in ('LeftHandMiddle3', 'RightHandMiddle3')}
        for k in range(n):
            fr = f0 + k * fps / 48; sc.frame_set(int(fr), subframe=fr - int(fr))
            for b in pts:
                pts[b].append(tuple(rig.matrix_world @ rig.pose.bones[b].tail))
        out.setdefault(label, {})[clip] = {b: [sum((p[i] - q[i]) ** 2 for i in range(3)) ** .5 * 1000
                                              for p, q in zip(v[1:], v[:-1])] for b, v in pts.items()}
        print('TIPS', label, clip, act.name, n, 'max', round(max(out[label][clip]['LeftHandMiddle3']), 1))
json.dump(out, open(os.path.join(HERE, 'work', 'fingertips.json'), 'w'))
