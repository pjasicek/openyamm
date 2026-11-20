"""Symmetric, centred joints (edits work/joints_final.json in place, after arm_rings.py / joints_fix.py or
compose_joints.py). Meshy's auto-rig of the grafted peasant bodies came back lopsided: shoulders 6 cm apart in
x (0.123 vs -0.184), one clavicle on the midline, the neck and head 8-10 cm behind the neck, the knees 13 cm
in front of the legs. Uneven shoulders read as dislocated (user review of the old peasants).
- Midline x: the centre of the body's torso ring at chest height.
- Spine, neck, head: x on the midline; y on the ring centre of the skin at that height (torso within TORSO_X of the
  midline; the neck ring of the body shell for Neck and Head, the hair would pull a head-height slice back).
- Pairs (clavicle, upper arm, forearm, hand, thigh, calf, foot, toe): mirrored about the midline and averaged, so
  both sides share one distance, height and depth.
- Clavicle heads CLAV_X beside the midline at the shoulders' height and the neck's depth (the reference rigs').
- Spine1 halfway between Spine and Spine2 when Meshy stacked it on Spine.
- Knees on the hip -> ankle line at their height, KNEE_FWD in front of it (keeps the hinge plane).
Args: -- <step1 blend>"""
import bpy, sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
ob = bpy.data.objects['Body']
co = np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices])
gv = np.zeros(len(co), np.int32); ob.data.attributes['garment'].data.foreach_get('value', gv)
pc = np.zeros(len(co), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pc)
p = os.path.join(HERE, 'work', 'joints_final.json')
d = json.load(open(p)); J = {k: np.array(v) for k, v in d['joints'].items()}
CJ = os.path.join(HERE, 'creature.json')
SYM = json.load(open(CJ)).get('joints_sym', {}) if os.path.exists(CJ) else {}
TORSO_X, CLAV_X, KNEE_FWD = SYM.get('torso_x', 0.12), SYM.get('clav_x', 0.03), SYM.get('knee_fwd', 0.012)
BODY = np.isin(pc, SYM.get('body_pieces', [0]))     # the shell that carries the torso and neck (not the grafted head)
before = {k: v.copy() for k, v in J.items()}


def ring(z, half, xw, cx=0.0):
    m = BODY & (np.abs(co[:, 2] - z) < half) & (np.abs(co[:, 0] - cx) < xw)
    if m.sum() < 8:
        return None
    c = co[m]
    return np.array([(c[:, 0].min() + c[:, 0].max()) / 2, (c[:, 1].min() + c[:, 1].max()) / 2])


if abs(J['Spine1'][2] - J['Spine'][2]) < 0.03:      # Meshy put Spine01 6 mm above Spine02: the chest bent in one place
    J['Spine1'][2] = (J['Spine'][2] + J['Spine2'][2]) / 2
chest = ring(J['Spine2'][2], 0.015, TORSO_X)
cx = float(chest[0])
for k in ('Pelvis', 'Spine', 'Spine1', 'Spine2'):
    r = ring(J[k][2], 0.015, TORSO_X, cx)
    J[k][0] = cx
    if r is not None:
        J[k][1] = r[1]
neck = ring(J['Neck'][2], 0.012, SYM.get('neck_x', 0.07), cx)
J['Neck'][:2] = (cx, neck[1])
J['Head'][:2] = (cx, neck[1] + SYM.get('head_dy', 0.005))
for b in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot', 'Toe0'):
    L, R = J[f'L_{b}'], J[f'R_{b}']
    hx = ((L[0] - cx) - (R[0] - cx)) / 2
    y, z = (L[1] + R[1]) / 2, (L[2] + R[2]) / 2
    J[f'L_{b}'] = np.array([cx + hx, y, z]); J[f'R_{b}'] = np.array([cx - hx, y, z])
for s, sg in (('L', 1), ('R', -1)):
    J[f'{s}_Clavicle'] = np.array([cx + sg * CLAV_X, J['Neck'][1], J[f'{s}_UpperArm'][2]])
    th, ft = J[f'{s}_Thigh'], J[f'{s}_Foot']
    t = (th[2] - J[f'{s}_Calf'][2]) / (th[2] - ft[2])
    k = th + (ft - th) * t
    J[f'{s}_Calf'] = np.array([k[0], k[1] - KNEE_FWD, J[f'{s}_Calf'][2]])
for k in sorted(J):
    if np.linalg.norm(J[k] - before[k]) > 0.005:
        print('JSYM', k, 'moved cm', round(float(np.linalg.norm(J[k] - before[k])) * 100, 1), '->',
              [round(float(x), 3) for x in J[k]])
d['joints'] = {k: [float(x) for x in v] for k, v in J.items()}
d['joints_sym'] = {'midline_x': cx}
json.dump(d, open(p, 'w'), indent=1)
print('JSYM midline x', round(cx, 4), 'shoulder half width', round(float(J['L_UpperArm'][0] - cx), 3))
