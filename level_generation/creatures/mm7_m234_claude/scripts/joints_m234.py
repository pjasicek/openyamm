"""G3 joints for the gargoyle (Meshy's auto-rig put the spine and clavicles 26 cm in front of the chest and the shoulders
10 cm apart in height; the ring fit put both hips on the midline). Composition, mirrored for symmetry (x = +-mean|x|,
y and z the side average):
- spine: B_Pelvis/Spine/Spine1/Spine2/Neck/Head at the source rig's relative heights between the pelvis and the neck,
  each on the torso centreline (centroid of the |x| < 0.15 m slice of the body at that height);
- clavicles on the shoulder line at the source's fraction of the shoulder's x, 2 cm below it; the head joint (skull
  base) halfway between the neck centre and the head slice's centre (which spans the jutting muzzle);
- shoulders, elbows, wrists from the ring fits (work/joints.json); hips and knees: Meshy's hips, the knee averaged
  between Meshy and the ring fit;
- digitigrade legs: the source's 'Foot' joint is our HOCK (raised heel, ring fit) and 'Toe0' the ball of the toes
  (Meshy's toe base, mirrored): the long foot segment hock -> ball stands at ~70 deg.
Writes work/joints_final.json. Args: -- <step1 blend>"""
import bpy, sys, os, json
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda f: os.path.join(HERE, 'work', f)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
co = np.array([tuple(bpy.data.objects['Body'].matrix_world @ v.co) for v in bpy.data.objects['Body'].data.vertices])
F = json.load(open(W('joints.json')))['joints']; M = json.load(open(W('meshy_joints.json')))['joints']
SRC = json.load(open(W('source_rest.json')))
sh = lambda n: np.array(SRC[n]['head'])


def mirror(l, r):
    l, r = np.array(l), np.array(r); x = (abs(l[0]) + abs(r[0])) / 2; yz = (l[1:] + r[1:]) / 2
    return np.array([x, *yz]), np.array([-x, *yz])


J = {}
for k, src in (('UpperArm', F), ('Forearm', F), ('Hand', F), ('Thigh', M), ('Foot', F), ('Toe0', M)):
    J[f'L_{k}'], J[f'R_{k}'] = mirror(src[f'L_{k}'], src[f'R_{k}'])
kl = (np.array(F['L_Calf']) + np.array(M['L_Calf'])) / 2; kr = (np.array(F['R_Calf']) + np.array(M['R_Calf'])) / 2
J['L_Calf'], J['R_Calf'] = mirror(kl, kr)


def centre(z):
    s = co[(np.abs(co[:, 2] - z) < 0.015) & (np.abs(co[:, 0]) < 0.15)]
    return np.array([0.0, (s[:, 1].min() + s[:, 1].max()) / 2, z])


pel_z = (J['L_Thigh'][2] + 0.06); neck_z = float(F['Neck'][2])
s0, s1 = sh('B_Pelvis')[2], sh('B_Neck')[2]
for b in ('Pelvis', 'Spine', 'Spine1', 'Spine2', 'Neck'):
    f = (sh(f'B_{b}')[2] - s0) / (s1 - s0)
    J[b] = centre(pel_z + f * (neck_z - pel_z))
hc = centre(float(F['Head'][2]) + 0.03)            # the slice spans the jutting muzzle: the skull base sits behind it
J['Head'] = np.array([0.0, (hc[1] + J['Neck'][1]) / 2, hc[2]])
for s_ in 'LR':
    a = sh('B_Spine2'); c = sh(f'B_{s_}_Clavicle'); u = sh(f'B_{s_}_UpperArm')
    f = float(c[0] / u[0])                                  # the source clavicle sits on the shoulder line, inboard
    U = J[f'{s_}_UpperArm']
    J[f'{s_}_Clavicle'] = np.array([U[0] * f, U[1], U[2] - 0.02])
out = {'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()}}
json.dump(out, open(W('joints_final.json'), 'w'), indent=1)
for k in sorted(J):
    print('JOINTSFINAL', k, np.round(J[k], 3).tolist())
