"""Source-animation fault scan (batch-1 lesson: the m412 Walk jumped 3.9 cm in one frame): for every clip of a GLB,
world positions of head, pelvis, hands and feet at viewer frames (time x 48); prints the largest per-frame vertical
step of head/pelvis against the clip's median step, single-frame pops (a step much larger than both neighbours),
the lowest foot/hand height, the hand-to-torso-axis minimum (hand through the body) and how long Attack/Hit stay
still at the start (dead start). Usage: blender -b -P clip_scan.py -- <glb>  -> work/clip_scan.json"""
import bpy, json, os, sys
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
B = ['B_Head', 'B_Pelvis', 'B_L_Hand', 'B_R_Hand', 'B_L_Foot', 'B_R_Foot', 'B_Spine1', 'B_Spine2', 'B_Neck']
fps = sc.render.fps / sc.render.fps_base; report = {}
for act in bpy.data.actions:
    rig.animation_data.action = act; f0, f1 = act.frame_range
    n = int(round((f1 - f0) / fps * 48)) + 1; P = {b: [] for b in B}; Q = []
    for i in range(n):
        sc.frame_set(int(f0), subframe=0.0) if False else None
        fr = f0 + i / 48 * fps; sc.frame_set(int(fr), subframe=fr - int(fr))
        for b in B:
            pb = rig.pose.bones[b]; P[b].append(list(rig.matrix_world @ pb.head))
        Q.append([list(pb.matrix_basis.to_quaternion()) for pb in rig.pose.bones])
    P = {b: np.array(v) for b, v in P.items()}; Q = np.array(Q)
    r = {'frames': n}
    for b in ('B_Head', 'B_Pelvis'):
        dz = np.diff(P[b][:, 2]); a = np.abs(dz); med = float(np.median(a)) + 1e-6
        k = int(a.argmax()); pops = [int(j + 1) for j in range(1, len(a) - 1) if a[j] > 0.01 and a[j] > 2.5 * max(a[j - 1], a[j + 1])]
        r[b] = {'max_step_cm': round(float(a.max()) * 100, 2), 'at_frame': k + 1, 'median_step_cm': round(med * 100, 2),
                'range_cm': round(float(np.ptp(P[b][:, 2])) * 100, 1), 'pops': pops}
    r['min_foot_z_cm'] = round(float(min(P['B_L_Foot'][:, 2].min(), P['B_R_Foot'][:, 2].min())) * 100, 1)
    # hand to the torso axis (spine1 -> neck), in metres
    def axis_dist(p):
        a, b = P['B_Spine1'], P['B_Neck']; ab = b - a; t = np.clip(((p - a) * ab).sum(1) / (ab * ab).sum(1), 0, 1)
        return np.linalg.norm(p - (a + ab * t[:, None]), axis=1)
    r['hand_axis_min_cm'] = {h: [round(float(axis_dist(P[h]).min()) * 100, 1), int(axis_dist(P[h]).argmin())] for h in ('B_L_Hand', 'B_R_Hand')}
    mot = np.abs(np.diff(Q, axis=0)).max(axis=(1, 2)); moving = np.where(mot > 0.002)[0]
    r['still_at_start_s'] = round(float(moving[0]) / 48, 3) if len(moving) else None
    report[act.name] = r
    print('CLIP', act.name, json.dumps(r))
json.dump(report, open(os.path.join(HERE, 'work', 'clip_scan.json'), 'w'), indent=1)
