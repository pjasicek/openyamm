"""Source-animation scan of a GLB: every clip sampled at the viewer's 48 fps (viewer frame = time x 48). Per frame:
world height of the root, Thorax and Head and the lowest skinned vertex; reports the largest per-frame steps
(pops), each bone's peak angular step (jolts), the first frame where any bone has moved over 2 degrees from frame 0
(dead start, Attack/Hit) and the loop seam gap. Usage: blender -b -P clip_scan.py -- <glb>  -> work/clip_scan.json"""
import os, sys, json, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Wasp')
fps = sc.render.fps / sc.render.fps_base
res = {}
for act in bpy.data.actions:
    rig.animation_data.action = act
    f0, f1 = act.frame_range; dur = (f1 - f0) / fps; n = int(round(dur * 48)) + 1
    rows, rots = [], []
    for i in range(n):
        sc.frame_set(int(f0), subframe=0.0)
        fr = f0 + i / 48 * fps; sc.frame_set(int(fr), subframe=fr - int(fr))
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg)
        zs = [(body.matrix_world @ v.co).z for v in ev.data.vertices]
        hz = lambda b: (rig.matrix_world @ rig.pose.bones[b].head).z
        rows.append([hz('Thorax'), hz('Head'), min(zs)])
        rots.append([pb.matrix.to_quaternion() for pb in rig.pose.bones])
    a = np.array(rows); d = np.abs(np.diff(a, axis=0))
    names = [pb.name for pb in rig.pose.bones]
    qa = lambda q1, q2: min(np.degrees(q1.rotation_difference(q2).angle), 360 - np.degrees(q1.rotation_difference(q2).angle))
    ang = np.array([[qa(rots[i][k], rots[i + 1][k]) for k in range(len(names))]
                    for i in range(n - 1)])
    move0 = np.array([[qa(rots[0][k], rots[i][k]) for k in range(len(names))]
                      for i in range(n)]).max(1)
    first_move = int(np.argmax(move0 > 2.0)) if (move0 > 2.0).any() else None
    top = np.argsort(-ang.max(0))[:4]
    res[act.name] = dict(seconds=round(dur, 3), frames=n,
                         thorax_step_cm=round(float(d[:, 0].max() * 100), 2), thorax_step_at=int(d[:, 0].argmax() + 1),
                         head_step_cm=round(float(d[:, 1].max() * 100), 2), head_step_at=int(d[:, 1].argmax() + 1),
                         head_median_step_cm=round(float(np.median(d[:, 1]) * 100), 2),
                         lowest_m=round(float(a[:, 2].min()), 4), lowest_at=int(a[:, 2].argmin()),
                         loop_gap_cm=round(float(np.abs(a[-1, :2] - a[0, :2]).max() * 100), 2),
                         first_move_frame=first_move,
                         jolts=[(names[k], round(float(ang[:, k].max()), 1), int(ang[:, k].argmax() + 1),
                                 round(float(np.median(ang[:, k])), 1)) for k in top])
    res[act.name]['thorax_z_cm'] = [round(float(x * 100), 1) for x in a[:, 0]]
    print('CLIP', act.name, json.dumps(res[act.name]))
json.dump(res, open(os.path.join(HERE, 'work', 'clip_scan.json'), 'w'), indent=1)
