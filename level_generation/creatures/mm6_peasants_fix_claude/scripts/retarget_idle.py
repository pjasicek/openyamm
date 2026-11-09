#!/usr/bin/env python3
"""Replace one clip of an installed Mixamo-named actor GLB with a Mixamo library clip (user review 2026-10-30 of the MM6
female peasant: her hand-authored clasped Standing pose read badly). Source: dump_fbx_clip.py npz (Blender frame: the
source faces -Y, +Z up); target glTF frame: +Z forward, +Y up, +X left, so v_gltf = (x, z, -y).
Our rest is an A-pose and Mixamo's a T-pose, so arm bones are first swung onto the source's rest segment direction
(head -> main child); every copied bone then takes the source's world rotation change since its rest:
W(t) = Rs(t) Rs0^-1 Swing W0 (spine, neck and head without the swing: the source rest leans forward). Locals follow
the hierarchy. The hips and legs keep frame 0 of the replaced clip (the skirt chains were simulated for that stance;
moving the legs pushed them through the skirt), and so do the bones the source lacks (skirt and braid chains, the
knife); forearm twist bones keep their rest. Mesh, skin, textures, LODs and the other clips stay byte-identical.
Usage: retarget_idle.py in.glb out.glb <source npz> <clip name>"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gltf_rig import Glb, qmul, qinv, qrot

src_glb, out, npz, CLIP = sys.argv[1:5]
g = Glb(src_glb); S = np.load(npz)
names = [str(n) for n in S['names']]; sparent = [str(p) for p in S['parents']]
M = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.0]])


def q_wxyz_to_mat(q):
    w, x, y, z = np.moveaxis(q, -1, 0)
    return np.stack([np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], -1),
                     np.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], -1),
                     np.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1)], -2)


def mat_to_q(m):                                      # -> (x, y, z, w); Shepperd: stable for every angle up to 180 deg
    m = np.asarray(m, float); flat = m.reshape(-1, 3, 3); out = np.zeros((len(flat), 4))
    for k, r in enumerate(flat):
        t = np.trace(r)
        if t > 0:
            s = np.sqrt(t + 1) * 2; q = [(r[2, 1] - r[1, 2]) / s, (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s, s / 4]
        elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
            s = np.sqrt(1 + r[0, 0] - r[1, 1] - r[2, 2]) * 2
            q = [s / 4, (r[0, 1] + r[1, 0]) / s, (r[0, 2] + r[2, 0]) / s, (r[2, 1] - r[1, 2]) / s]
        elif r[1, 1] > r[2, 2]:
            s = np.sqrt(1 + r[1, 1] - r[0, 0] - r[2, 2]) * 2
            q = [(r[0, 1] + r[1, 0]) / s, s / 4, (r[1, 2] + r[2, 1]) / s, (r[0, 2] - r[2, 0]) / s]
        else:
            s = np.sqrt(1 + r[2, 2] - r[0, 0] - r[1, 1]) * 2
            q = [(r[0, 2] + r[2, 0]) / s, (r[1, 2] + r[2, 1]) / s, s / 4, (r[1, 0] - r[0, 1]) / s]
        out[k] = np.array(q) / np.linalg.norm(q)
    return out.reshape(m.shape[:-2] + (4,))


def arc(u, v):
    u = u / np.linalg.norm(u); v = v / np.linalg.norm(v)
    ax = np.cross(u, v); c = np.dot(u, v)
    if c < -0.9999:
        ax = np.cross(u, [1, 0, 0]) if abs(u[0]) < 0.9 else np.cross(u, [0, 1, 0]); return np.r_[ax / np.linalg.norm(ax), 0.0]
    q = np.r_[ax, 1 + c]
    return q / np.linalg.norm(q)


to_g = lambda R: M @ R @ M.T
Rs0 = mat_to_q(to_g(q_wxyz_to_mat(S['rest_q'])))                 # (bones, 4)
Rs = mat_to_q(to_g(q_wxyz_to_mat(S['pose_q'])))                  # (frames, bones, 4)
Ps0 = S['rest_p'] @ M.T; Ps = S['pose_p'] @ M.T
nf = Rs.shape[0]; times = np.arange(nf) / float(S['fps'])
T0, R0, S0 = g.rest(); WT0, WR0 = g.fk(T0[None], R0[None]); WT0, WR0 = WT0[0], WR0[0]
CHILD = {'Hips': 'Spine', 'Spine': 'Spine1', 'Spine1': 'Spine2', 'Spine2': 'Neck', 'Neck': 'Head'}
for s in ('Left', 'Right'):
    CHILD.update({f'{s}Shoulder': f'{s}Arm', f'{s}Arm': f'{s}ForeArm', f'{s}ForeArm': f'{s}Hand', f'{s}Hand': f'{s}HandMiddle1',
                  f'{s}UpLeg': f'{s}Leg', f'{s}Leg': f'{s}Foot', f'{s}Foot': f'{s}ToeBase'})
    for fi in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'):
        CHILD.update({f'{s}Hand{fi}1': f'{s}Hand{fi}2', f'{s}Hand{fi}2': f'{s}Hand{fi}3'})
P = 'mixamorig:'
LIMB = ('Shoulder', 'Arm', 'ForeArm', 'Hand')      # A-pose vs T-pose: limbs are swung onto the source rest first; the
KEEP = ('Hips', 'UpLeg', 'Leg', 'Foot', 'ToeBase')    # spine/neck/head take the motion only (the source rest leans), and
mapped = [i for i, n in enumerate(g.names) if n.startswith(P) and n in names
          and not any(n[len(P):].replace('Left', '').replace('Right', '') == k for k in KEEP)]   # hips and legs keep the old pose
swing = {}
for i in mapped:
    if not any(k in g.names[i] for k in LIMB):
        continue
    short = g.names[i][len(P):]; c = CHILD.get(short)
    if c and P + c in names and P + c in g.names:
        ds = Ps0[names.index(P + c)] - Ps0[names.index(g.names[i])]
        dt = WT0[g.node(P + c)] - WT0[i]
        swing[i] = arc(dt, ds)
# leaves (finger tips, toes, head) take their parent's swing
def get_swing(i):
    if not any(k in g.names[i] for k in LIMB):
        return np.array([0, 0, 0, 1.0])
    while i not in swing and i in g.parent:
        i = g.parent[i]
    return swing.get(i, np.array([0, 0, 0, 1.0]))


Wnew = {}
for i in mapped:
    si = names.index(g.names[i])
    delta = qmul(Rs[:, si], qinv(Rs0[si]))[...]
    Wnew[i] = qmul(delta, qmul(get_swing(i), WR0[i]))
# original clip frame 0 (constant pose of the bones the source lacks)
t_old = g.clip_times(CLIP); To, Ro, So = g.sample(CLIP, t_old[:1])
hips = g.node(P + 'Hips')
local_R = np.repeat(R0[None], nf, 0).copy(); local_T = np.repeat(T0[None], nf, 0).copy(); local_S = np.repeat(S0[None], nf, 0).copy()
for i in range(len(g.names)):
    if i in Wnew:
        continue
    if 'Twist' in g.names[i]:
        continue                                      # rest
    local_R[:, i] = Ro[0, i]; local_T[:, i] = To[0, i]; local_S[:, i] = So[0, i]
# hierarchy order: locals of mapped bones from their new world rotation and the parent's
order = []
def visit(i):
    if i in order:
        return
    if i in g.parent:
        visit(g.parent[i])
    order.append(i)
for i in range(len(g.names)):
    visit(i)
WR = np.zeros((nf, len(g.names), 4))
for i in order:
    p = g.parent.get(i)
    if i in Wnew:
        WR[:, i] = Wnew[i]
        local_R[:, i] = qmul(qinv(WR[:, p]), Wnew[i]) if p is not None else Wnew[i]
    else:
        WR[:, i] = qmul(WR[:, p], local_R[:, i]) if p is not None else local_R[:, i]
# replace the clip
a = g.anim(CLIP); a['channels'] = []; a['samplers'] = []
ti = g.add_acc(times.astype(np.float32)[:, None], 'SCALAR', minmax=True)
for i in range(len(g.names)):
    if not any(i == j for j in g.doc['skins'][0]['joints']) and i != hips:
        continue
    for path, data, typ in (('translation', local_T[:, i], 'VEC3'), ('rotation', local_R[:, i], 'VEC4'), ('scale', local_S[:, i], 'VEC3')):
        if path == 'rotation':
            data = data.copy()
            for k in range(1, nf):
                if np.dot(data[k], data[k - 1]) < 0:
                    data[k] = -data[k]
        a['samplers'].append({'input': ti, 'output': g.add_acc(data, typ), 'interpolation': 'LINEAR'})
        a['channels'].append({'sampler': len(a['samplers']) - 1, 'target': {'node': i, 'path': path}})
g.save(out)
print('RETARGET', CLIP, nf, 'frames', round(times[-1], 3), 's; bones from the source', len(Wnew))
