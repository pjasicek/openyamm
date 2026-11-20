"""G1 / H1: range of motion of the chosen source clips, per joint, as swing (segment direction away from rest) and
twist (roll about the segment) of the rest-relative local rotation, with the segment axis taken from joint heads
(imported tails are unusable). Also elbow flexion (angle between upper arm and forearm segments) and wrist bend
(hand segment vs forearm segment). Writes work/rom.json: per role and joint the extremes with their frames, and a
deduplicated list of extreme source poses (clip, frame, reasons) - the stress poses for G4.
Args: -- <role=set_glb:clip> ...   e.g. Attack=/path/1Hand.glb:SwordAttackR1"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Quaternion
args = sys.argv[sys.argv.index('--') + 1:]
roles = []
for a in args:
    role, rest = a.split('=', 1)
    glb, clip = rest.rsplit(':', 1)
    roles.append((role, glb, clip))
JOINTS = {   # joint -> child joint giving the segment axis
    'B_Spine': 'B_Spine1', 'B_Spine1': 'B_Spine2', 'B_Spine2': 'B_Neck', 'B_Neck': 'B_Head',
}
for s in ('L', 'R'):
    JOINTS.update({f'B_{s}_Clavicle': f'B_{s}_UpperArm', f'B_{s}_UpperArm': f'B_{s}_Forearm',
                   f'B_{s}_Forearm': f'B_{s}_Hand', f'B_{s}_Hand': f'B_{s}_Finger2',
                   f'B_{s}_Thigh': f'B_{s}_Calf', f'B_{s}_Calf': f'B_{s}_Foot'})
loaded = {}
report = {}
poses = {}


def load(glb):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=glb)
    return next(o for o in bpy.data.objects if o.type == 'ARMATURE')


cur = None
for role, glb, clip in roles:
    if cur != glb:
        arm = load(glb); cur = glb
        axes = {}
        for j, c in JOINTS.items():
            b, cb = arm.data.bones[j], arm.data.bones[c]
            axes[j] = (b.matrix_local.to_3x3().inverted() @ (cb.head_local - b.head_local)).normalized()
    acts = {x.name.split('@')[-1].split('|')[-1]: x for x in bpy.data.actions}
    act = acts[clip]
    arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    W = arm.matrix_world
    series = {j: {'swing': [], 'twist': []} for j in JOINTS}
    elbow = {'L': [], 'R': []}; wrist = {'L': [], 'R': []}
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        for j in JOINTS:
            q = arm.pose.bones[j].matrix_basis.to_quaternion().normalized()
            ax = axes[j]
            v = Vector((q.x, q.y, q.z))
            tw = 2 * math.atan2(v.dot(ax), q.w)
            tw = (tw + math.pi) % (2 * math.pi) - math.pi
            sw = ax.angle(q @ ax)
            series[j]['swing'].append(math.degrees(sw)); series[j]['twist'].append(math.degrees(tw))
        for s in ('L', 'R'):
            p = {n: W @ arm.pose.bones[f'B_{s}_{n}'].head for n in ('UpperArm', 'Forearm', 'Hand', 'Finger2')}
            up, fo, ha = p['Forearm'] - p['UpperArm'], p['Hand'] - p['Forearm'], p['Finger2'] - p['Hand']
            elbow[s].append(math.degrees(up.angle(fo))); wrist[s].append(math.degrees(fo.angle(ha)))
    rr = {}
    for j, d in series.items():
        sw, tw = np.array(d['swing']), np.array(d['twist'])
        rr[j] = {'swing_max': round(float(sw.max()), 1), 'swing_frame': int(f0 + sw.argmax()),
                 'twist_min': round(float(tw.min()), 1), 'twist_max': round(float(tw.max()), 1),
                 'twist_frames': [int(f0 + tw.argmin()), int(f0 + tw.argmax())]}
    for s in ('L', 'R'):
        e, w = np.array(elbow[s]), np.array(wrist[s])
        rr[f'{s}_elbow_flex'] = {'min': round(float(e.min()), 1), 'max': round(float(e.max()), 1), 'frame_max': int(f0 + e.argmax())}
        rr[f'{s}_wrist_bend'] = {'min': round(float(w.min()), 1), 'max': round(float(w.max()), 1), 'frame_max': int(f0 + w.argmax())}
    report[role] = {'clip': clip, 'frames': [f0, f1], 'joints': rr}
    # extreme poses for the weight gate: arm joints and spine, per clip
    for j in [k for k in JOINTS if 'Clavicle' in k or 'Arm' in k or 'Forearm' in k or 'Hand' in k or 'Spine' in k]:
        r = rr[j]
        poses.setdefault((role, r['swing_frame']), []).append(f'{j} swing {r["swing_max"]}')
        for fr, val in zip(r['twist_frames'], (r['twist_min'], r['twist_max'])):
            if abs(val) > 25:
                poses.setdefault((role, fr), []).append(f'{j} twist {val}')
    for s in ('L', 'R'):
        poses.setdefault((role, rr[f'{s}_elbow_flex']['frame_max']), []).append(f'{s} elbow {rr[f"{s}_elbow_flex"]["max"]}')
        poses.setdefault((role, rr[f'{s}_wrist_bend']['frame_max']), []).append(f'{s} wrist {rr[f"{s}_wrist_bend"]["max"]}')
out = {'roles': report, 'stress_poses': [{'role': r, 'frame': f, 'why': w} for (r, f), w in sorted(poses.items())]}
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'rom.json')
json.dump(out, open(path, 'w'), indent=1)
print('ROM written', path, 'stress poses', len(out['stress_poses']))
for role, r in report.items():
    j = r['joints']
    print(f"ROM {role:9s} R_UpperArm swing {j['B_R_UpperArm']['swing_max']:6.1f} twist [{j['B_R_UpperArm']['twist_min']:6.1f},{j['B_R_UpperArm']['twist_max']:6.1f}]"
          f" | R_Forearm twist [{j['B_R_Forearm']['twist_min']:6.1f},{j['B_R_Forearm']['twist_max']:6.1f}]"
          f" | R elbow [{j['R_elbow_flex']['min']:5.1f},{j['R_elbow_flex']['max']:5.1f}] R wrist max {j['R_wrist_bend']['max']:5.1f}"
          f" | L elbow max {j['L_elbow_flex']['max']:5.1f} | R clav swing {j['B_R_Clavicle']['swing_max']:5.1f}"
          f" | Spine1 swing {j['B_Spine1']['swing_max']:5.1f}")
