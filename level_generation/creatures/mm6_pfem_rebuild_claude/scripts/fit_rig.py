#!/usr/bin/env python3
"""Joints of MM9's PeasantFemale skeleton (73 joints, names and rest rotations kept) TRANSLATED onto the assembled v3 body (work/asm.npz,
Blender frame, MM9 origin; raw ABC: 'L' at -x). Every joint gets a position here (build_glb.py keeps MM9's world rotations):
- spine chain at MM9's heights mapped pelvis..shoulder onto ours, on our torso's mid-depth line; Head pivot at the skull base (ear height,
  as mm9_peasantf1_claude: a bow turns the face over the collar instead of driving the chin into it);
- clavicles beside our neck; arms on the MM9 bind direction the assembly used (shoulder, elbow, wrist), fingers at the MPFB joints;
- legs at the v3 knee/ankle/ball joints (paired from the v3 right leg);
- skirt chains: MM9's azimuths, heights mapped waist..hem onto our shorter, wider skirt, radius = our skirt surface (MM9's chains sit on
  its surface too); XCOM_skirt at our belt;
- Ponytail11/12 on our braid (root at the nape, middle), Ponytail1 / XCOM_Hair / xpony with the head.
Args: <asm npz> <mm9 glb> <out json>"""
import sys, json
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
from rig_bones import SKIRT_CHAINS
A, MM9, OUT = sys.argv[1:4]
D = np.load(A); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(names)}
V3 = {k: np.array(v) for k, v in json.loads(str(D['v3joints'])).items()}
hj = json.loads(str(D['hj']))
m = Model(Glb(MM9)); nn = [n.get('name') for n in m.glb.json['nodes']]; w0 = m.world({})
MJ = {n: np.array([w0[i][0, 3], -w0[i][2, 3], w0[i][1, 3]]) for i, n in enumerate(nn) if n}
parent = {}
for i, n in enumerate(m.glb.json['nodes']):
    for c in n.get('children', []): parent[nn[c]] = nn[i]
from meshlib import sample
PT = {n: sample(co, tri[comp[tri[:, 0]] == pid[n]], 200000, k)[0] for k, n in enumerate(names)}
P = lambda n: PT[n]
J = {}
dress = P('dress'); mid = dress[np.abs(dress[:, 0]) < 0.05]


def mid_y(z, pts=mid, band=0.012, back=0.15):
    q = pts[np.abs(pts[:, 2] - z) < band]
    return float(q[:, 1].min() + (q[:, 1].max() - q[:, 1].min()) * (0.5 + back * 0.5)) if len(q) else 0.0


sh = D['sh']; el = D['el']; wr = D['wr']                       # +x side (raw 'R')
pel_z = float(V3['mixamorig:Hips'][2]); shz = float(sh[2])
zmap = lambda z: pel_z + z * (shz - pel_z) / MJ['FHP R UpperArm'][2]
J['Scene Root'] = MJ['Scene Root']
J['FHP Pelvis'] = np.array([0, mid_y(pel_z + 0.06, np.vstack([mid, P('skirt')[np.abs(P('skirt')[:, 0]) < 0.05]]), 0.03), pel_z])
for b in ('FHP Spine1', 'FHP Spine2', 'FHP Spine3', 'FHP Neck'):
    z = zmap(MJ[b][2]); J[b] = np.array([0, mid_y(z), z])
HZ = 0.605 + (zmap(MJ['FHP Head'][2]) - MJ['FHP Head'][2]) * 0.0
hs = np.vstack([P('head'), dress[dress[:, 2] > J['FHP Neck'][2]]]); hs = hs[np.abs(hs[:, 0]) < 0.04]
J['FHP Head'] = np.array([0, mid_y(HZ, hs, 0.01, 0.1), HZ])
for s, sg in (('L', -1), ('R', 1)):
    J[f'FHP {s} Clavicle'] = np.array([sg * 0.038, J['FHP Neck'][1], J['FHP Neck'][2] - 0.012])
    J[f'FHP {s} UpperArm'] = sh * [sg, 1, 1]; J[f'FHP {s} Forearm'] = el * [sg, 1, 1]; J[f'FHP {s} Hand'] = wr * [sg, 1, 1]
    for a, b in (('Calf', 'mixamorig:RightLeg'), ('Foot', 'mixamorig:RightFoot'), ('Toe0', 'mixamorig:RightToeBase')):
        J[f'FHP {s} {a}'] = V3[b] * [-sg, 1, 1]
# ---- skirt: waist on the belt, chains on our skirt surface
belt = P('belt'); WZ = float(0.5 * (belt[:, 2].min() + belt[:, 2].max()))
sk = P('skirt'); HEMZ = float(sk[:, 2].min()); TOPZ = float(sk[:, 2].max())
cy = float(0.5 * (sk[:, 1].min() + sk[:, 1].max()))
J['XCOM_skirt'] = np.array([0, mid_y(WZ, np.vstack([mid, belt]), 0.02), WZ])
mz_w, mz_h = MJ['XCOM_skirt'][2], np.mean([MJ[c[-1]][2] for c in SKIRT_CHAINS])
mmesh = None


def skirt_r(pts, cyy, az, z, band=0.02, wid=0.22):
    q = pts[np.abs(pts[:, 2] - z) < band]
    if not len(q): return None
    th = np.arctan2(q[:, 1] - cyy, q[:, 0]); k = np.abs(((th - az + np.pi) % (2 * np.pi)) - np.pi) < wid
    return float(np.hypot(q[k, 0], q[k, 1] - cyy).max()) if k.any() else None


# MM9's own skirt radius: chain joints sit on its surface (measured ratio 0.94-1.05), so the joint radius is MM9's surface radius
rep = {}
for ch in SKIRT_CHAINS:
    for b in ch[1:]:
        j = MJ[b]; az = float(np.arctan2(j[1] - MJ['XCOM_skirt'][1], j[0])); rm = float(np.hypot(j[0], j[1] - MJ['XCOM_skirt'][1]))
        z = WZ + (j[2] - mz_w) * (HEMZ - WZ) / (mz_h - mz_w)
        zz = min(z, TOPZ - 0.02)
        ro = skirt_r(sk, cy, az, zz)
        if ro is None or j[2] > mz_w - 0.03:                    # at or above the waist: MM9's radius ratio to the waist
            rw_o = skirt_r(np.vstack([belt, sk]), cy, az, WZ - 0.02, 0.03) or rm; ro = rm * 1.0
        r = 0.98 * ro
        J[b] = np.array([r * np.cos(az), cy + r * np.sin(az), z]); rep[b] = [round(rm, 3), round(r, 3), round(float(j[2]), 3), round(z, 3)]
# ---- braid on the Ponytail chain: 11 at the braid's root (its top, inside), 12 half way down
br = P('braid'); top = br[br[:, 2] > br[:, 2].max() - 0.03]; bot = br[br[:, 2] < br[:, 2].min() + 0.03]
r11 = np.array([0, float(np.median(top[:, 1])) - 0.01, float(br[:, 2].max()) - 0.03])
r12 = np.array([0, float(np.median(br[np.abs(br[:, 2] - (r11[2] + br[:, 2].min()) / 2) < 0.02][:, 1])), float((r11[2] + br[:, 2].min()) / 2)])
J['FHP Ponytail11'] = r11; J['FHP Ponytail12'] = r12
dH = J['FHP Head'] - MJ['FHP Head']
for n in ('FHP Ponytail1', 'XCOM_Hair') + tuple(x for x in MJ if x.startswith('xpony')):
    J[n] = MJ[n] + dH
# anything left: with its nearest placed ancestor
for n in MJ:
    if n in J or n.endswith('.mesh') or n in ('NGon01', 'F1a'): continue
    p = parent.get(n)
    while p is not None and p not in J: p = parent.get(p)
    J[n] = MJ[n] + ((J[p] - MJ[p]) if p else 0)
F = {}
for nm, k in zip(('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'), range(1, 6)):
    F[nm] = [hj[f'finger{k}-1'], hj[f'finger{k}-2'], hj[f'finger{k}-3'], hj[f'finger{k}-3_tip']]
palm = np.cross(np.array(hj['finger2-1']) - wr, np.array(hj['finger5-1']) - wr); palm /= np.linalg.norm(palm)
moves = {n: round(float(np.linalg.norm(J[n] - MJ[n])) * 100, 1) for n in J if n in MJ}
json.dump(dict(joints={k: np.asarray(v).tolist() for k, v in J.items()}, fingers=F, palm=palm.tolist(), mm9={k: v.tolist() for k, v in MJ.items()},
               waist=WZ, hem=HEMZ, skirt_cy=cy, moves_cm=moves, skirt=rep), open(OUT, 'w'), indent=0)
print('RIG', {k: np.round(J[k], 3).tolist() for k in ('FHP Pelvis', 'FHP Spine1', 'FHP Spine3', 'FHP Neck', 'FHP Head', 'FHP R Clavicle', 'FHP R UpperArm', 'FHP R Hand', 'FHP R Calf', 'FHP R Foot', 'FHP R Toe0', 'XCOM_skirt', 'xrt4', 'xfr4', 'xbk4', 'FHP Ponytail11', 'FHP Ponytail12')})
print('MOVES cm max', max(moves.values()), 'waist', round(WZ, 3), 'hem', round(HEMZ, 3))
