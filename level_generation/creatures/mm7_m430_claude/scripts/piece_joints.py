"""G3 joints for the m430 wight: the arms, legs and spine are hidden in the robe, so Meshy's auto-rig estimate
(work/meshy_joints.json) is kept for the spine and arms (its wrists sit ~9 cm below the sleeve openings, where a ~20 cm
hand inside the long hand pieces starts; the open boundary loop of each hand piece is reported for comparison). The
LEGS are rebuilt: Meshy put them leaning 20 cm forward with the ankles 14-20 cm above the floor inside the robe; they
now hang straight under its hip joints (knee 0.50 m, ankle 0.08 m, toe 12 cm ahead), mirrored symmetric.
Mirror differences are reported.
Writes work/joints_final.json. Args: -- <blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']
co = np.array([tuple(v.co) for v in ob.data.vertices])
pv = np.zeros(len(co), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
M = {k: np.array(v) for k, v in json.load(open(os.path.join(HERE, 'work', 'meshy_joints.json')))['joints'].items()}
J = {k: v.copy() for k, v in M.items()}
bm = bmesh.new(); bm.from_mesh(ob.data)
for s, p in (('L', 1), ('R', 2)):
    b = sorted({v.index for e in bm.edges if e.is_boundary for v in e.verts if pv[v.index] == p})
    w = co[b].mean(0)
    print('JOINTS', s, 'wrist from', len(b), 'boundary verts', np.round(w, 3).tolist(), 'meshy off cm', round(float(np.linalg.norm(w - M[f'{s}_Hand'])) * 100, 1))
for s, sg in (('L', 1), ('R', -1)):
    hx = (abs(M['L_Thigh'][0]) + abs(M['R_Thigh'][0])) / 2 * sg; hy = (M['L_Thigh'][1] + M['R_Thigh'][1]) / 2; hz = (M['L_Thigh'][2] + M['R_Thigh'][2]) / 2
    J[f'{s}_Thigh'] = np.array([hx, hy, hz]); J[f'{s}_Calf'] = np.array([hx * 1.05, hy - 0.01, 0.50])
    J[f'{s}_Foot'] = np.array([hx * 1.1, hy + 0.01, 0.08]); J[f'{s}_Toe0'] = np.array([hx * 1.1, hy - 0.11, 0.02])
for a in ('UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot'):
    l, r = J[f'L_{a}'], J[f'R_{a}']
    print('SYM', a, 'L', np.round(l, 3).tolist(), 'R', np.round(r, 3).tolist(), 'mirror diff cm', round(float(np.linalg.norm(l - r * np.array([-1, 1, 1]))) * 100, 1))
json.dump({'height_m': float(co[:, 2].max() - co[:, 2].min()), 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()}},
          open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
