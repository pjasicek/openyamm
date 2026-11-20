"""World bind frames (glTF frame) for every node of our rig (from mm9_evilsorcerer_claude/scripts/build_glb.py).
Each Bip01 bone's bind frame is MM9's rest frame turned by the least rotation onto our bone (so MM9's local rotations
give MM9's poses); the hand by fingers + thumb directions; finger chains take MM9's Finger1/Finger0 frames; wing bones
keep MM9's local transform under our Spine2, with the wing root moved so it stands as far behind our back as MM9's
stands behind MM9's. Half-joint helpers take the child's frame.
Writes {order, parent, world (4x4 lists), wing_heads (Blender frame)}. Args: <rig json> <mm9 glb> <asm npz> <out json>"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
from rig_bones import FINGERS, half_pairs, WING_L, WING_R
from meshlib import section
RIG, MM9, ASM, OUT = sys.argv[1:5]
R = json.load(open(RIG)); JB, FB = R['joints'], R['fingers']
def g(p): return np.array([p[0], p[2], -p[1]], float)       # Blender -> glTF
def b(p): return np.array([p[0], -p[2], p[1]], float)       # glTF -> Blender
# hinge pivots toward the outside of the bend (collapse lesson): +y Blender is the back
for s_ in 'LR':
    JB[f'Bip01 {s_} Calf'][1] -= 0.0; JB[f'Bip01 {s_} Forearm'][1] += 0.012
src = Model(Glb(MM9)); sdoc = src.glb.json; snodes = sdoc['nodes']
sn = [n.get('name') for n in snodes]; six = {n: i for i, n in enumerate(sn)}; W0 = src.world({})
def smat(n): return W0[six[n]].copy()
parent = {}
for i, n in enumerate(snodes):
    for c in n.get('children', []): parent[sn[c]] = sn[i]
JOINTS = [n for n in sn if n and (n.startswith('Bip01') or n.startswith('Bone') or n == 'Scene Root')]
P = {n: g(JB[n]) for n in JB}
def unit(v): return v / np.linalg.norm(v)
def least(a, b_):
    a, b_ = unit(a), unit(b_); v = np.cross(a, b_); c = a @ b_; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
CHILD = {'Bip01 Spine': 'Bip01 Spine1', 'Bip01 Spine1': 'Bip01 Spine2', 'Bip01 Spine2': 'Bip01 Spine3', 'Bip01 Spine3': 'Bip01 Neck', 'Bip01 Neck': 'Bip01 Head'}
for s in 'LR':
    CHILD.update({f'Bip01 {s} Clavicle': f'Bip01 {s} UpperArm', f'Bip01 {s} UpperArm': f'Bip01 {s} Forearm', f'Bip01 {s} Forearm': f'Bip01 {s} Hand',
                  f'Bip01 {s} Thigh': f'Bip01 {s} Calf', f'Bip01 {s} Calf': f'Bip01 {s} Foot', f'Bip01 {s} Foot': f'Bip01 {s} Toe0'})
W = {'Scene Root': smat('Scene Root')}
order = []
def visit(n):
    order.append(n)
    for k in snodes[six[n]].get('children', []):
        if sn[k] in JOINTS: visit(sn[k])
visit('Scene Root')
# wing root offset: MM9's root depth behind MM9's back, kept behind ours
D = np.load(ASM); co, tri, comp = D['co'], D['tri'], D['comp']
body_t = tri[comp[tri[:, 0]] == 0]
mm_root = b(smat('Bone13')[:3, 3])
def back_y(P_, T_, z, x):
    L = section(P_, T_, np.array([0, 0, z]), np.array([0, 0, 1.0]))
    ys = [p[1] for l in L for p in l['pts'] if abs(p[0] - x) < 0.03]
    return max(ys) if ys else None
import importlib.util
spec = importlib.util.spec_from_file_location('mm9_mesh', str(HERE / 'scripts' / 'mm9_mesh.py')); mm = importlib.util.module_from_spec(spec); spec.loader.exec_module(mm)
M9 = mm.load(MM9); mco, mtri, mjw, mww, mjn = M9['co'], M9['tri'], M9['jw'], M9['ww'], M9['jnames']
dom = np.array([mjn[mjw[i][np.argmax(mww[i])]] for i in range(len(mco))])
key = np.round(mco, 4); u_, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); MT = inv[mtri]
wingv = np.zeros(len(u_), bool); wingv[inv[np.array([d.startswith('Bone') for d in dom])]] = True
MT = MT[~wingv[MT].any(1)]
mm_back = back_y(u_, MT, mm_root[2], mm_root[0])
for n in order[1:]:
    Rm = smat(n)[:3, :3]
    if n in P:
        Dm = np.eye(3)
        if n.endswith(' Foot'):
            c = CHILD[n]; a_ = smat(c)[:3, 3] - smat(n)[:3, 3]; b_ = P[c] - P[n]; a_[1] = 0; b_[1] = 0; Dm = least(a_, b_)
        elif n in CHILD:
            c = CHILD[n]; Dm = least(smat(c)[:3, 3] - smat(n)[:3, 3], P[c] - P[n])
        elif n.endswith('Hand'):
            mir = -1 if ' L ' in n else 1; pre = n[:-4]
            m_d = smat(pre + 'Finger2')[:3, 3] - smat(n)[:3, 3]; m_t = smat(pre + 'Finger0')[:3, 3] - smat(n)[:3, 3]
            o_d = g([FB['Middle'][0][0] * mir, FB['Middle'][0][1], FB['Middle'][0][2]]) - P[n]; o_t = g([FB['Thumb'][0][0] * mir, FB['Thumb'][0][1], FB['Thumb'][0][2]]) - P[n]
            def frame(a, c_):
                x = unit(a); z = unit(np.cross(x, c_)); return np.c_[x, np.cross(z, x), z]
            Dm = frame(o_d, o_t) @ frame(m_d, m_t).T
        elif n.endswith('Toe0'):
            mir = -1 if ' L ' in n else 1; Dm = least(Rm[:, 0], np.array([-0.08 * mir, 0, 1.0]))
        Mx = np.eye(4); Mx[:3, :3] = Dm @ Rm; Mx[:3, 3] = P[n]; W[n] = Mx
    else:
        pn = parent[n]; Lm = np.linalg.inv(smat(pn)) @ smat(n); W[n] = W[pn] @ Lm
# move both wing roots (Bone48 / Bone13) in depth so they keep MM9's distance behind the back
shift = {}
for root in ('Bone48', 'Bone13'):
    rb = b(W[root][:3, 3]); ob = back_y(co, body_t, rb[2], rb[0])
    mb = back_y(u_, MT, b(smat(root)[:3, 3])[2], b(smat(root)[:3, 3])[0])
    want = ob + (b(smat(root)[:3, 3])[1] - mb)
    dy = want - rb[1]; shift[root] = round(float(dy), 4)
    delta = g([0, dy, 0])
    stack = [root]
    while stack:
        x = stack.pop(); W[x] = W[x].copy(); W[x][:3, 3] += delta
        stack += [c for c in order if parent.get(c) == x]
print('wing root depth shift (m)', shift, 'MM9 root behind back', round(float(mm_root[1] - mm_back), 3))
# half joints, fingers
for h, c, pn, _ in half_pairs():
    W[h] = W[c].copy(); order.append(h); parent[h] = pn
for s_, mir in (('L', -1), ('R', 1)):
    pre = f'Bip01 {s_} '
    for f in FINGERS:
        pts = [g([p[0] * mir, p[1], p[2]]) for p in FB[f]]
        src_f = pre + {'Thumb': 'Finger0', 'Index': 'Finger1', 'Middle': 'Finger2', 'Ring': 'Finger3', 'Pinky': 'Finger4'}[f]
        Rf = W[pre + 'Hand'][:3, :3] @ smat(pre + 'Hand')[:3, :3].T @ smat(src_f)[:3, :3]
        dirn = unit(pts[1] - pts[0]); Rf = least(Rf[:, 0], dirn) @ Rf       # x along our finger, MM9's curl axes
        for k in range(3):
            n = f'{pre}{f}{k + 1}'
            Mx = np.eye(4); Mx[:3, :3] = Rf; Mx[:3, 3] = pts[k]; W[n] = Mx
            order.append(n); parent[n] = pre + 'Hand' if k == 0 else f'{pre}{f}{k}'
# wing pleat helpers (pleat_keys.py): one per membrane panel, at the wrist, in the wrist bone's frame
for a, wrist in (('A', 'Bone50'), ('B', 'Bone15')):
    for k in (1, 2, 3):
        n = f'XPleat{a}{k}'; W[n] = W[wrist].copy(); order.append(n); parent[n] = wrist
wing_heads = {n: b(W[n][:3, 3]).tolist() for n in WING_L + WING_R}
for n in ('Bip01 Spine2', 'Bip01 Spine1', 'Bip01 Spine3'): wing_heads[n] = b(W[n][:3, 3]).tolist()
json.dump(dict(order=order, parent=parent, world={n: W[n].tolist() for n in order}, wing_heads=wing_heads), open(OUT, 'w'))
print('BIND', len(order), 'nodes')
