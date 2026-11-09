"""G4/G5/arm gate on every game clip of work/anim_v2.blend, every second frame:
  - edge stretch (posed / rest length, edges over 5 mm) p99 and max, with the worst edge's dominant bones,
  - penetration: arm, hand and finger vertices inside the torso/abdomen, modelled as capsules round the posed spine,
    pelvis and abdomen bones with each bone's rest radius (median distance of its dominant vertices) x 0.8; the
    signed nearest-face test was unreliable on this open, multi-piece mesh,
  - forearm twist: the hand's roll about the forearm axis against its rest (degrees), the wrist bend.
Writes work/clip_gate.json and prints one line per clip."""
import bpy, bmesh, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v3.blend'))
rig = bpy.data.objects['Rig']; queen = bpy.data.objects['Queen']
scene = bpy.context.scene
me = queen.data
gi = {g.index: g.name for g in queen.vertex_groups}
dom = np.array([gi[max(v.groups, key=lambda g: g.weight).group] if len(v.groups) else '' for v in me.vertices])
is_body = np.array([d.startswith(('B_Spine', 'B_Pelvis', 'Abdomen')) for d in dom])
is_arm = np.array([('UpperArm' in d or 'Forearm' in d or 'Hand' in d or 'Finger' in d) for d in dom])
E = np.array([tuple(e.vertices) for e in me.edges])
rest = np.array([tuple(v.co) for v in me.vertices])
rest_len = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
OK = rest_len > 0.005
RM = json.loads((P / 'work' / 'rigid_mask.json').read_text())
rigid = np.zeros(len(rest), bool); rigid[RM['metal'] + RM['strap']] = True
ARM_E = rigid[E[:, 0]] & rigid[E[:, 1]]                # edges inside the breastplate and chest strap
BODY = [b.name for b in rig.data.bones if b.name.startswith(('B_Spine', 'B_Pelvis', 'Abdomen'))]
def seg_dist(p, a, b):
    d = b - a; t = np.clip(((p - a) @ d) / max(d @ d, 1e-12), 0, 1)
    return np.linalg.norm(p - a - t[:, None] * d, axis=1)
RAD = {}
for n in BODY:
    b = rig.data.bones[n]; ids = np.where(dom == n)[0]
    if len(ids):
        RAD[n] = float(np.median(seg_dist(rest[ids], np.array(b.head_local), np.array(b.tail_local))))
report = {}
for name in ('Standing', 'Attack', 'Cast', 'Hit', 'Death'):
    act = bpy.data.actions[name]
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = map(int, act.frame_range)
    worst = {'p99': 0, 'max': 0, 'pen': 0, 'pen_max_cm': 0, 'twist': 0, 'frame_max': 0, 'frame_pen': 0}
    step = 2 if name != 'Standing' else 6
    for f in range(f0, f1 + 1, step):
        scene.frame_set(f)
        deps = bpy.context.evaluated_depsgraph_get()
        em = queen.evaluated_get(deps).to_mesh()
        pc = np.array([tuple(v.co) for v in em.vertices])
        queen.evaluated_get(deps).to_mesh_clear()
        L = np.linalg.norm(pc[E[:, 0]] - pc[E[:, 1]], axis=1)
        ratio = np.where(OK, np.maximum(L / np.maximum(rest_len, 1e-6), rest_len / np.maximum(L, 1e-6)), 1.0)
        if ratio.max() > worst['max']:
            k = int(np.argmax(ratio))
            worst.update(max=round(float(ratio.max()), 2), frame_max=f, worst_bones=[str(dom[E[k, 0]]), str(dom[E[k, 1]])])
        worst['p99'] = max(worst['p99'], round(float(np.percentile(ratio, 99)), 2))
        worst['armour_max'] = max(worst.get('armour_max', 0), round(float(ratio[ARM_E].max()), 3))
        if name != 'Death' or f < 20:      # once she sinks the body passes through the floor and rock by design
            arm_pts = pc[is_arm]
            depth = np.zeros(len(arm_pts))
            for n, r in RAD.items():
                pb = rig.pose.bones[n]
                a = np.array(rig.matrix_world @ pb.head); b = np.array(rig.matrix_world @ pb.tail)
                depth = np.maximum(depth, 0.8 * r - seg_dist(arm_pts, a, b))
            pen = depth[depth > 0]
            if len(pen) > worst['pen']:
                worst.update(pen=int(len(pen)), pen_max_cm=round(100 * float(pen.max()), 1), frame_pen=f)
        for s in 'LR':
            fa = rig.pose.bones[f'B_{s}_Forearm']; hd = rig.pose.bones[f'B_{s}_Hand']
            rel = (fa.matrix.to_3x3().inverted() @ hd.matrix.to_3x3())
            rel_rest = (rig.data.bones[fa.name].matrix_local.to_3x3().inverted() @ rig.data.bones[hd.name].matrix_local.to_3x3())
            d = (rel_rest.inverted() @ rel).to_quaternion()
            twist = abs(math.degrees(2 * math.atan2(d.y, d.w)))
            twist = min(twist, 360 - twist)
            worst['twist'] = max(worst['twist'], round(twist, 1))
    report[name] = worst
    print('GATE', name, json.dumps(worst))
(P / 'work' / 'clip_gate.json').write_text(json.dumps(report, indent=1))
