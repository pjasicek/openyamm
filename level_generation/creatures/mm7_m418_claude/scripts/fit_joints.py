"""G3 joints of the m418 troglodyte, measured on the step1 skin (Meshy's auto-rig put the left hand on the tail and the
knees 0.5 m apart in depth, so none of its joints are used). Sources, at the 1.7 m working scale (y forward = -):
- arms: geodesic rings from the middle claw (limb_profiles.py): wrist = the first narrow ring above the claws (r 4 cm),
  elbow = closest approach of line fits to the forearm rings (d 0.48-0.66) and the upper-arm rings (d 0.82-1.02),
  shoulder = where the rings merge into the body (r jumps above 9 cm);
- legs: horizontal slices (the leg is one blob per slice): ankle = the lowest shin slice above the foot, knee = the
  most forward slice centre, hip = the thigh line continued to the pelvis height; ball of the foot where the three
  toes split;
- spine: the body's midline (x -0.075 from vertical slices) through the hump's centre, from the pelvis between the
  hips forward and up to the hood's rim (the groove at y -0.95); clavicles just inside the shoulders;
- tail: B_Tail0 from behind the pelvis, then centroids of the geodesic rings from the tail tip (the tail curves to
  the creature's left in the rest pose).
Writes work/joints_final.json ('joints' in build_rig.py's names plus 'tail': the chain's points, root to tip).
Args: none"""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(HERE, 'work', 'limb_profiles.json')))
X0 = -0.075                                                     # body midline


def ring(name, d):
    return np.array(next(p['c'] for p in P[name]['profile'] if abs(p['d'] - d) < 1e-6))


def line_fit(name, d0, d1):
    pts = np.array([p['c'] for p in P[name]['profile'] if d0 - 1e-6 <= p['d'] <= d1 + 1e-6])
    c = pts.mean(0); u = np.linalg.svd(pts - c)[2][0]
    return c, u


def closest(c1, u1, c2, u2):
    w = c1 - c2; a, b, cc, d, e = u1 @ u1, u1 @ u2, u2 @ u2, u1 @ w, u2 @ w
    t = (b * e - cc * d) / (a * cc - b * b); s = (a * e - b * d) / (a * cc - b * b)
    return (c1 + u1 * t + c2 + u2 * s) / 2


J = {}
for s, hand, sh in (('R', 'R_hand', 1.04), ('L', 'L_hand', 1.0)):
    J[f'{s}_Hand'] = ring(hand, 0.48)
    J[f'{s}_Forearm'] = closest(*line_fit(hand, 0.48, 0.66), *line_fit(hand, 0.82, 1.02))
    J[f'{s}_UpperArm'] = ring(hand, sh)
    J[f'{s}_Clavicle'] = np.array([X0 + (J[f'{s}_UpperArm'][0] - X0) * 0.35, -0.86, 1.16])
# legs from the slices (scratch slices.py runs, recorded here)
J.update({'R_Foot': np.array([-0.49, -0.37, 0.17]), 'R_Calf': np.array([-0.52, -0.71, 0.53]),
          'R_Thigh': np.array([-0.37, -0.50, 0.80]), 'R_Toe0': np.array([-0.55, -0.62, 0.07]),
          'L_Foot': np.array([0.32, -0.21, 0.17]), 'L_Calf': np.array([0.37, -0.63, 0.53]),
          'L_Thigh': np.array([0.22, -0.50, 0.80]), 'L_Toe0': np.array([0.31, -0.46, 0.07])})
J.update({'Pelvis': np.array([X0, -0.42, 0.88]), 'Spine': np.array([X0, -0.55, 1.0]), 'Spine1': np.array([X0, -0.68, 1.1]),
          'Spine2': np.array([X0, -0.80, 1.17]), 'Neck': np.array([X0, -0.92, 1.2]), 'Head': np.array([X0, -1.0, 1.2])})
tail = [np.array([-0.03, -0.15, 0.88]), np.array([0.05, 0.15, 0.80])] + [ring('tail', d) for d in (1.4, 1.1, 0.84, 0.56, 0.3)] + \
    [np.array(P['tail']['tip'])]
for k in ('Hand', 'Forearm', 'UpperArm'):
    l, r = J[f'L_{k}'], J[f'R_{k}']
    print('SYM', k, np.round(r, 3).tolist(), np.round(l, 3).tolist(), 'mirror diff cm',
          round(float(np.linalg.norm((l - [X0, 0, 0]) * [-1, 1, 1] - (r - [X0, 0, 0]))) * 100, 1))
print('JOINTS tail bones', len(tail) - 1, 'length m', round(float(sum(np.linalg.norm(np.diff(tail, axis=0), axis=1))), 3))
json.dump({'height_m': 1.7, 'joints': {k: [round(float(x), 4) for x in v] for k, v in J.items()},
           'tail': [[round(float(x), 4) for x in v] for v in tail]},
          open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
