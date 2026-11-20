"""Final weights by part from the heat weights. Args: <asm npz> <heat npz> <rig json> <labels npy> <out npz>"""
import sys, json, os
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from rig_bones import FINGERS, half_pairs, PANELS, panel_bones
J_, H_, R_, L_, OUT = sys.argv[1:6]
D = np.load(J_); co, tri, comp = D['co'], D['tri'], D['comp']; pn = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(pn)}
H = np.load(H_); W = H['W'].astype(np.float64); names = [str(x) for x in H['names']]
extra = [b for k in PANELS for b in panel_bones(k)]
for n in ('Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck', 'Bip01 Head', 'Bip01 L Clavicle', 'Bip01 R Clavicle'):
    if n not in names: extra.append(n)
names = names + extra; W = np.c_[W, np.zeros((len(W), len(extra)))]
ix = {n: i for i, n in enumerate(names)}
labels = np.load(L_)
P = lambda n: comp == pid[n]
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def swap(n): return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ')
perm = np.array([ix.get(swap(n), ix[n]) for n in names])
d, m = cKDTree(co * [-1, 1, 1]).query(co)
print('mirror max', d.max())
W = 0.5 * (W + W[m][:, perm])
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(co), len(co))).tocsr(); A.data[:] = 1
deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
def smooth(mask, passes):
    global W
    for _ in range(passes):
        S = (A @ W) / deg[:, None]
        W[mask] = 0.5 * W[mask] + 0.5 * S[mask]
fingers = labels > 0
skin = P('torso') | P('legs') | P('boots') | P('shoes')
smooth(skin, int(os.environ.get('PASSES', '6')))
sj = np.array(json.load(open(R_))['joints']['Bip01 L UpperArm'])
zone = (np.minimum(np.linalg.norm(co - sj, axis=1), np.linalg.norm(co - sj * [-1, 1, 1], axis=1)) < 0.15) & P('torso')
smooth(zone, int(os.environ.get('SHPASS', '8')))
def only(mask, *bones):
    """keep only these bones, renormalised; a vertex with none left takes the first"""
    keep = np.zeros(W.shape[1]); keep[[ix[b] for b in bones]] = 1
    W[mask] *= keep; s = W[mask].sum(1); ids = np.where(mask)[0]
    W[ids[s < 1e-6], ix[bones[0]]] = 1
def rigid(mask, b): W[mask] = 0; W[mask, ix[b]] = 1
# hands: their own chain and the hand; palm no finger bones of other fingers
for lab, f in enumerate(FINGERS, 1):
    for s, sgn in (('L', -1), ('R', 1)):
        vs = (labels == lab) & (co[:, 0] * sgn > 0)
        only(vs, f'Bip01 {s} Hand', *[f'Bip01 {s} {f}{k}' for k in (1, 2, 3)])
for s, sgn in (('L', -1), ('R', 1)):
    rest = P('hands') & (labels == 0) & (co[:, 0] * sgn > 0)
    allow = [f'Bip01 {s} Hand'] + [f'Bip01 {s} {f}1' for f in FINGERS] + [f'Bip01 {s} Thumb2']
    only(rest, *allow)
    rigid(P('bracers') & (co[:, 0] * sgn > 0), f'Bip01 {s} Forearm')
    rigid(P('greaves') & (co[:, 0] * sgn > 0), f'Bip01 {s} Calf')
    # boots keep leg weights only
    only(P('boots') & (co[:, 0] * sgn > 0), f'Bip01 {s} Calf', f'Bip01 {s} Foot')
    only(P('shoes') & (co[:, 0] * sgn > 0), f'Bip01 {s} Foot', f'Bip01 {s} Toe0')
    only(P('legs') & (co[:, 0] * sgn > 0), f'Bip01 {s} Thigh', f'Bip01 {s} Calf', 'Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1')
    rigid(P('pauldrons') & (co[:, 0] * sgn > 0), f'Bip01 {s} UpperArm')    # moved to the half joint below
# knee and elbow: a tight blend round the joint (heat spreads it over a third of the limb on this sparse mesh, the leg reads as rubber)
JJ = json.load(open(R_))['joints']
for s, sgn in (('L', -1), ('R', 1)):
    for pr, a, b, c, rad, part in ((f'Bip01 {s} ', 'Thigh', 'Calf', 'Foot', 0.075, 'legs'), (f'Bip01 {s} ', 'UpperArm', 'Forearm', 'Hand', 0.075, 'torso')):
        ja, jb, jc = [np.array(JJ[pr + k]) for k in (a, b, c)]
        ax = (jc - ja) / np.linalg.norm(jc - ja)
        t = (co - jb) @ ax
        sel = P(part) & (co[:, 0] * sgn > 0) & ((W[:, ix[pr + a]] + W[:, ix[pr + b]]) > 0.2)
        if part == 'torso': sel &= t > -0.16
        tot = W[sel, ix[pr + a]] + W[sel, ix[pr + b]]
        bl = ss(t[sel], -rad, rad)
        W[sel, ix[pr + a]] = tot * (1 - bl); W[sel, ix[pr + b]] = tot * bl
# head: rigid; the neck tube blends into the neck bone below the jaw
hv = P('head'); hb = np.array(json.load(open(R_))['joints']['Bip01 Head'])
rigid(hv | P('crown') | P('eyes'), 'Bip01 Head')
r = np.hypot(co[:, 0], co[:, 1] - 0.0)
neck = hv & (r < 0.078) & (co[:, 2] < 1.73)
u = ss(co[:, 2] + 0.45 * (-co[:, 1]), 1.655, 1.74)       # jaw line: higher behind
W[neck] = 0; W[neck, ix['Bip01 Neck']] = 1 - u[neck]; W[neck, ix['Bip01 Head']] = u[neck]
# torso collar follows the neck bone
col = P('torso') & (co[:, 2] > 1.60) & (np.abs(co[:, 0]) < 0.13)
t = ss(co[:, 2], 1.60, 1.64)
W[col] = W[col] * (1 - t[col])[:, None]; W[col, ix['Bip01 Neck']] += t[col]
# parts that sit on the torso: nearest torso vertex, smoothed along themselves
src = np.where(P('torso'))[0]; kd = cKDTree(co[src])
for nm, passes in (('yokeF', 10), ('yokeB', 10)):
    q = np.where(P(nm))[0]; W[q] = W[src[kd.query(co[q])[1]]]; smooth(P(nm), passes)
# belt: nearest of torso or hip, a ring must not shear
src2 = np.where(P('torso') | P('legs'))[0]; kd2 = cKDTree(co[src2])
q = np.where(P('belt'))[0]; W[q] = W[src2[kd2.query(co[q])[1]]]
only(P('belt'), 'Bip01 Spine', 'Bip01 Pelvis', 'Bip01 Spine1')
smooth(P('belt'), 30)
b = P('buckle'); W[b] = W[np.where(P('belt') & (co[:, 1] < -0.1))[0]].mean(0)
# hip flaps ride on the thigh under them: weights of the nearest leg point, the top under the belt follows the pelvis
ls = np.where(P('legs'))[0]; kd3 = cKDTree(co[ls])
for nm in ('flapF', 'flapB'):
    q = np.where(P(nm))[0]; dist, near = kd3.query(co[q], k=3)
    wt = 1 / np.maximum(dist, 1e-4); wt /= wt.sum(1, keepdims=True)
    W[q] = (W[ls[near]] * wt[..., None]).sum(1)
    top = ss(co[q, 2], 1.02, 1.14)
    W[q] = W[q] * (1 - top)[:, None]; W[q, ix['Bip01 Pelvis']] += top
    smooth(P(nm), 8)
# panels: links by height
for k, nm in (('F', 'panelF'), ('B', 'panelB')):
    q = np.where(P(nm))[0]; z = co[q, 2]; Z = PANELS[k]; bn = panel_bones(k)
    W[q] = 0
    for i, v in enumerate(q):
        zz = z[i]
        if zz >= Z[0] + 0.01: W[v, ix['Bip01 Pelvis']] = 1; continue
        if zz >= Z[0] - 0.05:
            u_ = ss(Z[0] + 0.01 - zz, 0.0, 0.06); W[v, ix['Bip01 Pelvis']] = 1 - u_; W[v, ix[bn[0]]] = u_; continue
        for j in range(1, len(Z)):
            if zz >= Z[j] - 0.05 or j == len(Z) - 1:
                if j == len(Z) - 1 and zz < Z[j] - 0.05: W[v, ix[bn[j]]] = 1; break
                if zz >= Z[j] + 0.05: W[v, ix[bn[j - 1]]] = 1
                else:
                    u_ = ss(Z[j] + 0.05 - zz, 0.0, 0.10); W[v, ix[bn[j - 1]]] = 1 - u_; W[v, ix[bn[j]]] = u_
                break
# half joints
pairs = half_pairs()
names = names + [h for h, _, _, _ in pairs]
W = np.c_[W, np.zeros((len(W), len(pairs)))]; ix = {n: i for i, n in enumerate(names)}
rigidparts = P('crown') | P('eyes') | P('hands') | P('bracers') | P('greaves') | P('buckle')
for h, c, _, ps in pairs:
    ic = ix[c]; ip = [ix[x] for x in ps]
    a = W[:, ip].sum(1); b = W[:, ic]; m_ = np.minimum(a, b)
    sel = (m_ > 1e-4) & ~rigidparts & ~P('pauldrons')
    W[sel, ix[h]] = 2 * m_[sel]; W[sel, ic] -= m_[sel]
    W[np.ix_(np.where(sel)[0], ip)] *= (1 - m_[sel] / a[sel])[:, None]
# pauldrons: rigid plates on the upper arm's half joint
for s, sgn in (('L', -1), ('R', 1)):
    v = P('pauldrons') & (co[:, 0] * sgn > 0); W[v] = 0; W[v, ix[f'Bip01 {s} XhalfUpperArm']] = 1
ord_ = np.argsort(-W, axis=1)[:, :4]
ww = np.take_along_axis(W, ord_, 1); ww = np.where(ww < 0.012, 0, ww); ww /= ww.sum(1, keepdims=True)
print('max influences used', (ww > 1e-3).sum(1).max(), 'unweighted', int((W.sum(1) < 1e-5).sum()), {pn[k]: int((W[comp == k].sum(1) < 1e-5).sum()) for k in range(len(pn)) if (W[comp == k].sum(1) < 1e-5).any()})
np.savez(OUT, wj=ord_, ww=ww.astype('f4'), wnames=np.array(names))
