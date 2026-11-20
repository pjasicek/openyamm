"""Source-animation scan per clip at the viewer's 48 fps (viewer frame = time x 48): world height of the head and
pelvis bones and the lowest body vertex per frame, the largest single-frame height steps (pops), frames with the
body under the floor, and the "dead start" of one-shot clips (time until any bone has moved 1 cm or 2 degrees from
frame 0). Usage: blender -b -P clip_scan.py -- <glb> -> work/clip_scan.json"""
import json, math, os, sys, bpy, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers))
fps = sc.render.fps / sc.render.fps_base; report = {}
for act in bpy.data.actions:
    rig.animation_data.action = act; f0, f1 = act.frame_range; dur = (f1 - f0) / fps
    rows = []
    for k in range(int(round(dur * 48)) + 1):
        t = k / 48; fr = f0 + t * fps; sc.frame_set(int(math.floor(fr)), subframe=fr - math.floor(fr))
        head = (rig.matrix_world @ rig.pose.bones['B_Head'].head).z; pel = (rig.matrix_world @ rig.pose.bones['B_Pelvis'].head).z
        b = bmesh.new(); b.from_object(body, bpy.context.evaluated_depsgraph_get()); b.transform(body.matrix_world)
        low = min(v.co.z for v in b.verts); b.free()
        mats = [rig.matrix_world @ pb.matrix for pb in rig.pose.bones]
        rows.append((head, pel, low, mats))
    H = np.array([r[0] for r in rows]); Pz = np.array([r[1] for r in rows]); L = np.array([r[2] for r in rows])
    dh, dp = np.diff(H), np.diff(Pz)
    moved = None
    for k, r in enumerate(rows):
        dmax = max((m.translation - m0.translation).length for m, m0 in zip(r[3], rows[0][3]))
        amax = max(math.degrees((m.to_quaternion().rotation_difference(m0.to_quaternion())).angle) for m, m0 in zip(r[3], rows[0][3]))
        if dmax > .01 or amax > 2:
            moved = k; break
    top = np.argsort(-np.abs(dh))[:3]
    report[act.name] = {'duration_s': round(dur, 3), 'frames_48': len(rows),
                        'head_range_cm': round(float(np.ptp(H)) * 100, 1), 'pelvis_range_cm': round(float(np.ptp(Pz)) * 100, 1),
                        'largest_head_steps_cm': [(int(k), int(k + 1), round(float(dh[k]) * 100, 2)) for k in top],
                        'largest_pelvis_step_cm': round(float(np.abs(dp).max()) * 100, 2),
                        'below_floor_cm': round(float(min(L.min(), 0)) * 100, 2), 'below_floor_frames': [int(k) for k in np.where(L < -0.01)[0]],
                        'first_motion_frame': moved}
    report[act.name]["pelvis_cm"] = [round(float(x) * 100, 2) for x in Pz]
    print("SCAN", act.name, json.dumps({k: v for k, v in report[act.name].items() if k != "pelvis_cm"}), flush=True)
json.dump(report, open(os.path.join(HERE, 'work', 'clip_scan.json'), 'w'), indent=1)
