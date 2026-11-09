"""G3 joints of the m178 devil at the 1.7 m working scale (y forward = -), measured on the step1 skin (piece 0).
Meshy's auto-rig (work/meshy_joints.json) is the second estimate; it was usable for the legs, elbows and hips but not
in depth for the trunk: the shoulders 22 cm behind the back, the spine/neck/head on the chest and throat surface.
- arms (arm_rings.py, rings perpendicular to the local arm axis from a shoulder seed inside the torso): wrist = the
  narrowest ring before the palm widens (perimeter 23-24 cm), elbow = closest approach of the upper-arm and forearm
  line fits (within 2 cm of Meshy's); shoulder = the upper-arm line 6 cm under the shoulder top (z 1.21);
- legs (body_slices.py horizontal slices; each leg one loop): knee = closest approach of the thigh (z 0.66-0.82) and
  shin (z 0.38-0.52) line fits; hip = the thigh line at Meshy's hip height; ankle = the leg loop centre at z 0.25
  (just above the heel spur and the high slate foot top; Meshy's ankle is within 1 cm); ball of the foot = Meshy's;
- trunk: slice loop centres with the spine kept 4-5 cm toward the back (a spine is posterior); neck at the base of the
  skull's throat cut, head pivot behind and below the jaw;
- tail: centroids of the geodesic rings from the tail tip (body_slices.py), root where the tail leaves the pelvis.
Writes work/joints_final.json ('joints' in build_rig.py's names plus 'tail'). Args: none"""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda *p: os.path.join(HERE, 'work', *p)
D = json.load(open(W('body_slices.json')))
M = {k: np.array(v) for k, v in json.load(open(W('meshy_joints.json')))['joints'].items()}
A = json.load(open(W('arm_rings.json')))
CL = json.load(open(W('centrelines.json')))


def line_fit(p):
    c = p.mean(0); u = np.linalg.svd(p - c)[2][0]
    return c, (u if u[2] > 0 else -u)


def closest(c1, u1, c2, u2):
    w = c1 - c2; a, b, cc, d, e = u1 @ u1, u1 @ u2, u2 @ u2, u1 @ w, u2 @ w
    t = (b * e - cc * d) / (a * cc - b * b); s = (a * e - b * d) / (a * cc - b * b)
    return (c1 + u1 * t + c2 + u2 * s) / 2


def at_z(c, u, z):
    return c + u * (z - c[2]) / u[2]


J = {}
for s, sx in (('L', 1), ('R', -1)):
    J[f'{s}_Hand'] = np.array(A['joints'][f'{s}_Hand'])
    J[f'{s}_Forearm'] = np.array(A['joints'][f'{s}_Forearm'])
    cl = np.array(CL[f'{s}_arm'])
    up = cl[(cl[:, 2] < 1.15) & (cl[:, 2] > J[f'{s}_Forearm'][2] + 0.06)]
    J[f"{s}_UpperArm"] = at_z(*line_fit(up), 1.21)              # joint centre ~6 cm under the shoulder top (z 1.27)
    J[f"{s}_Clavicle"] = np.array([sx * 0.04, -0.61, 1.26])
    leg = {float(z): [r for r in rs if np.sign(r['c'][0]) == sx and abs(r['c'][0]) < 0.3 and r['per'] > 0.2]
           for z, rs in D['legs'].items()}
    pts = lambda z0, z1: np.array([min(rs, key=lambda r: abs(r['c'][0]))['c'] for z, rs in leg.items() if z0 <= z <= z1 and rs])
    th, sh = line_fit(pts(0.66, 0.82)), line_fit(pts(0.38, 0.52))
    J[f'{s}_Calf'] = closest(*th, *sh)
    J[f'{s}_Thigh'] = at_z(*th, M[f'{s}_Thigh'][2])
    J[f'{s}_Foot'] = np.array(min(leg[0.26], key=lambda r: abs(r['c'][0]))['c'])
    J[f'{s}_Toe0'] = M[f'{s}_Toe0']
    for k in ('Thigh', 'Calf', 'Foot', 'Forearm', 'Hand', 'UpperArm'):
        print('JOINTS', s, k, np.round(J[f'{s}_{k}'], 3).tolist(), 'meshy off cm', round(float(np.linalg.norm(J[f'{s}_{k}'] - M[f'{s}_{k}'])) * 100, 1))
J.update({'Pelvis': np.array([0.0, -0.53, 0.93]), 'Spine': np.array([0.0, -0.55, 1.03]), 'Spine1': np.array([0.0, -0.565, 1.13]),
          'Spine2': np.array([0.0, -0.575, 1.23]), 'Neck': np.array([0.0, -0.60, 1.33]), 'Head': np.array([0.0, -0.645, 1.40])})
T = D['tail']['profile']
tc = lambda d: np.array(min(T, key=lambda p: abs(p['d'] - d))['c'])
tail = [np.array([0.0, -0.42, 0.90])] + [tc(d) for d in (1.30, 1.10, 0.90, 0.70, 0.50, 0.32, 0.16)] + [np.array(D['tail']['tip'])]
for t in tail:
    t[0] = 0.0                                                   # the mesh is mirror-symmetric (|x| of the centroids < 3 cm)
for k in ('Hand', 'Forearm', 'UpperArm', 'Thigh', 'Calf', 'Foot'):
    l, r = J[f'L_{k}'], J[f'R_{k}']
    print('SYM', k, 'mirror diff cm', round(float(np.linalg.norm(l * [-1, 1, 1] - r)) * 100, 1))
print('JOINTS tail bones', len(tail) - 1, 'length m', round(float(sum(np.linalg.norm(np.diff(tail, axis=0), axis=1))), 3))
json.dump({'height_m': 1.7, 'joints': {k: [round(float(x), 4) for x in v] for k, v in J.items()},
           'tail': [[round(float(x), 4) for x in v] for v in tail]}, open(W('joints_final.json'), 'w'), indent=1)
