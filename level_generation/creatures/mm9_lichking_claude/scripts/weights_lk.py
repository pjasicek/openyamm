"""Final weights by part from the heat weights (Lich King). Args: <asm npz> <heat npz> <rig json> <labels npy> <out npz>
Heat weights on the skin parts (torso shell with coat, pants, boots, upper-arm tubes, hands) are mirror-averaged and smoothed; then by part:
fingers on their own chain, bracers on the forearm, tight blends at knees and elbows, crown and skull rigid on the head, small plates take the
weights of the torso under them, the tabard rides a four-link chain, the coat below the belt rides seven two-link hinge sectors (coat_keys.py)."""
import sys, json, os
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from rig_bones import FINGERS, half_pairs, PANELS, panel_bones, COAT, COAT_Z, coat_bones, wrist
J_, H_, R_, L_, OUT = sys.argv[1:6]
D = np.load(J_); co, tri, comp = D['co'], D['tri'], D['comp']; pn = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(pn)}
H = np.load(H_); W = H['W'].astype(np.float64); names = [str(x) for x in H['names']]
if len(W) < len(co): W = np.r_[W, np.zeros((len(co) - len(W), W.shape[1]))]          # staff parts appended after the heat run
extra = [b for k in PANELS for b in panel_bones(k)] + [b for k in COAT for b in coat_bones(k)]
for n in ('Bone01', 'Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck', 'Bip01 Head', 'Bip01 L Clavicle', 'Bip01 R Clavicle'):
    if n not in names: extra.append(n)
names = names + extra; W = np.c_[W, np.zeros((len(W), len(extra)))]
ix = {n: i for i, n in enumerate(names)}
labels = np.load(L_)
if len(labels) < len(co): labels = np.r_[labels, np.zeros(len(co) - len(labels), int)]
R = json.load(open(R_)); JJ = R['joints']
P = lambda n: comp == pid[n]
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def swap(n): return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ').replace('XCoatSL', 'XCoat_S').replace('XCoatSR', 'XCoatSL').replace('XCoat_S', 'XCoatSR')
perm = np.array([ix.get(swap(n), ix[n]) for n in names])
# heat bones are named by the bone table: the wrist bone differs per side (L Finger0, R Hand)
body = ~np.isin(comp, [pid[n] for n in ('staff', 'sskull', 'cap', 'tubecap') if n in pid]); bi = np.where(body)[0]
d, m = cKDTree(co[bi] * [-1, 1, 1]).query(co); m = bi[m]; d[~body] = 0
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
def only(mask, *bones):
    keep = np.zeros(W.shape[1]); keep[[ix[b] for b in bones]] = 1
    W[mask] *= keep; s = W[mask].sum(1); ids = np.where(mask)[0]
    W[ids[s < 1e-6], ix[bones[0]]] = 1
def rigid(mask, b): W[mask] = 0; W[mask, ix[b]] = 1
def side(s): return co[:, 0] * (-1 if s == 'L' else 1) > 0
smooth(P('torso') | P('pants') | P('boots') | P('uarms'), int(os.environ.get('PASSES', '6')))
# torso shell: no leg or hand bones; the coat part below is replaced further down
upper = ['Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck']
for s in 'LR': upper += [f'Bip01 {s} Clavicle', f'Bip01 {s} UpperArm']
only(P('torso'), *upper)
sj = np.array(JJ['Bip01 R UpperArm'])
zone = (np.minimum(np.linalg.norm(co - sj, axis=1), np.linalg.norm(co - sj * [-1, 1, 1], axis=1)) < 0.16) & P('torso')
smooth(zone, 10)
for s in 'LR':
    pre = f'Bip01 {s} '; wr = wrist(s); sd = side(s)
    for lab, f in enumerate(FINGERS, 1):
        only((labels == lab) & sd, wr, *[f'{pre}{f}{k}' for k in (1, 2, 3)])
    only(P('hands') & (labels == 0) & sd, wr, *[f'{pre}{f}1' for f in FINGERS], pre + 'Thumb2')
    rigid(P('bracers') & sd, pre + 'Forearm')
    rigid(P('kneemed') & sd, pre + 'Calf')
    only(P('boots') & sd, pre + 'Thigh', pre + 'Calf', pre + 'Foot')
    only(P('pants') & sd, pre + 'Thigh', pre + 'Calf', 'Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1')
    only(P('uarms') & sd, pre + 'Clavicle', pre + 'UpperArm', pre + 'Forearm', 'Bip01 Spine3')
    # knee, ankle and elbow: tight blends round the joint
    for a, b, c, rad, parts in (('Thigh', 'Calf', 'Foot', 0.07, ('pants', 'boots')), ('UpperArm', 'Forearm', 'Hand', 0.06, ('uarms',))):
        ja, jb, jc = [np.array(JJ[pre + k]) for k in (a, b, c)]
        ax = (jc - ja) / np.linalg.norm(jc - ja); t = (co - jb) @ ax
        sel = np.isin(comp, [pid[p] for p in parts]) & sd & ((W[:, ix[pre + a]] + W[:, ix[pre + b]]) > 0.2)
        tot = W[sel, ix[pre + a]] + W[sel, ix[pre + b]]; bl = ss(t[sel], -rad, rad)
        W[sel, ix[pre + a]] = tot * (1 - bl); W[sel, ix[pre + b]] = tot * bl
    bt = P('boots') & sd; ank = np.array(JJ[pre + 'Foot'])
    u = ss(co[:, 2], ank[2] + 0.02, ank[2] + 0.08)        # 0 at the sole, 1 above the ankle
    fw = (1 - u) * (W[:, ix[pre + 'Calf']] + W[:, ix[pre + 'Foot']] + W[:, ix[pre + 'Thigh']])
    W[bt, ix[pre + 'Foot']] = (1 - u[bt]) + u[bt] * W[bt, ix[pre + 'Foot']] * 0
    W[bt, ix[pre + 'Calf']] *= u[bt]; W[bt, ix[pre + 'Thigh']] *= u[bt]
# staff and its skull: rigid on MM9's staff bone (under R Hand)
if 'staff' in pid: rigid(P('staff') | P('sskull'), 'Bone01')
# tube caps: each cap vertex takes the weights of the rim vertex it was built on (the centre takes the rim's first)
if 'tubecap' in pid:
    q = np.where(P('tubecap'))[0]; W[q] = W[D['tubecap_src']]
# r9: the upper chest plate (front, |x| < 16 cm, z 1.10-1.36) rides the spine, not the clavicles: with the arms raised (AttackMelee, Taunt)
# MM9's clavicle turns folded 43-55 chest faces between Spine3 and the clavicles. Clavicle and upper-arm shares fade out towards the
# midline (full at |x| 16 cm, none at 7 cm) and go to Spine3, then the band is smoothed.
cb = P('torso') | P('collar') | P('wings')
chest = cb & (co[:, 1] < 0.02) & (co[:, 2] > 1.10) & (co[:, 2] < 1.36) & (np.abs(co[:, 0]) < 0.16)
fx = ss(np.abs(co[:, 0]), 0.07, 0.16)
for s_ in 'LR':
    for bn in (f'Bip01 {s_} Clavicle', f'Bip01 {s_} UpperArm'):
        moved = W[chest, ix[bn]] * (1 - fx[chest]); W[chest, ix[bn]] -= moved; W[chest, ix['Bip01 Spine3']] += moved
smooth(chest, int(os.environ.get('CHEST_PASSES', '3')))
rigid(P('skull') | P('crown') | (P('cap') if 'cap' in pid else False), 'Bip01 Head')
# collar ring: neck at the top, upper chest below
q = P('collar'); t = ss(co[:, 2], 1.30, 1.37)
W[q] = 0; W[q, ix['Bip01 Neck']] = 0.35 + 0.65 * t[q]; W[q, ix['Bip01 Spine3']] = 0.65 - 0.65 * t[q]
# small plates: weights of the torso under them
src = np.where(P('torso'))[0]; kd = cKDTree(co[src])
for nm, passes in (('wings', 6), ('medal', 6), ('medalsF', 6), ('medalsB', 6)):
    qq = np.where(P(nm))[0]; dist, near = kd.query(co[qq], k=4); wt = 1 / np.maximum(dist, 1e-4); wt /= wt.sum(1, keepdims=True)
    W[qq] = (W[src[near]] * wt[..., None]).sum(1); smooth(P(nm), passes)
# medallions again on the fixed chest
for nm, passes in (('medal', 6), ('medalsF', 6)):
    qq = np.where(P(nm))[0]; dist, near = kd.query(co[qq], k=4); wt = 1 / np.maximum(dist, 1e-4); wt /= wt.sum(1, keepdims=True)
    W[qq] = (W[src[near]] * wt[..., None]).sum(1); smooth(P(nm), passes)
# coat below the belt: two-link hinge sectors by azimuth and height
cz0, cz1 = COAT_Z
az = np.degrees(np.arctan2(co[:, 0], co[:, 1]))       # 0 at the back (+y), +90 at +x
coat = P('torso') & (co[:, 2] < cz0 + 0.04)
sk = list(COAT); sa = np.array([COAT[k] for k in sk])
ci = np.where(coat)[0]
for v in ci:
    a = az[v]; dd = np.abs(((a - sa) + 180) % 360 - 180)
    o = np.argsort(dd)[:2]; d0, d1 = dd[o[0]], dd[o[1]]
    w0 = 1.0 if d0 + d1 < 1e-6 else d1 / (d0 + d1); w0 = w0 * w0 * (3 - 2 * w0); w1 = 1 - w0
    if d0 > 60: w0, w1 = 1.0, 0.0                       # front of the side sectors: nearest only
    z = co[v, 2]
    top = ss(z, cz0 - 0.03, cz0 + 0.04)                 # 1 above the belt hinge: stays on the spine
    low = ss(cz1 + 0.05 - z, 0.0, 0.10)                  # 1 below the knee hinge
    keep = W[v].copy(); W[v] = 0
    for kk, ww in ((sk[o[0]], w0), (sk[o[1]], w1)):
        b1, b2 = coat_bones(kk)
        W[v, ix[b1]] += ww * (1 - top) * (1 - low); W[v, ix[b2]] += ww * (1 - top) * low
    W[v] += top * keep * 0 + top * np.eye(W.shape[1])[ix['Bip01 Spine']] * 0.6 + top * np.eye(W.shape[1])[ix['Bip01 Pelvis']] * 0.4 if top > 0 else 0
smooth(coat, 3)
# belt line of the shell and the buckle: spine and pelvis
q = np.where(P('buckle'))[0]; W[q] = 0; W[q, ix['Bip01 Spine']] = 0.6; W[q, ix['Bip01 Pelvis']] = 0.4
# tabard: links by height under the spine
for k, nm in (('F', 'tabard'),):
    q = np.where(P(nm))[0]; z = co[q, 2]; Z = PANELS[k]; bn = panel_bones(k)
    W[q] = 0
    for i, v in enumerate(q):
        zz = z[i]
        if zz >= Z[0] + 0.01: W[v, ix['Bip01 Spine']] = 1; continue
        if zz >= Z[0] - 0.05:
            u_ = ss(Z[0] + 0.01 - zz, 0.0, 0.06); W[v, ix['Bip01 Spine']] = 1 - u_; W[v, ix[bn[0]]] = u_; continue
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
rigidparts = (P('staff') | P('sskull') | P('cap') if 'staff' in pid else False) | P('crown') | P('skull') | P('hands') | P('bracers') | P('buckle') | P('kneemed') | P('tabard')
for h, c, _, ps in pairs:
    ic = ix[c]; ip = [ix[x] for x in ps]
    a = W[:, ip].sum(1); b = W[:, ic]; m_ = np.minimum(a, b)
    sel = (m_ > 1e-4) & ~rigidparts
    W[sel, ix[h]] = 2 * m_[sel]; W[sel, ic] -= m_[sel]
    W[np.ix_(np.where(sel)[0], ip)] *= (1 - m_[sel] / a[sel])[:, None]
ord_ = np.argsort(-W, axis=1)[:, :4]
ww = np.take_along_axis(W, ord_, 1); ww = np.where(ww < 0.012, 0, ww); ww /= ww.sum(1, keepdims=True)
print('max influences used', (ww > 1e-3).sum(1).max(), 'unweighted', int((W.sum(1) < 1e-5).sum()), {pn[k]: int((W[comp == k].sum(1) < 1e-5).sum()) for k in range(len(pn)) if (W[comp == k].sum(1) < 1e-5).any()})
np.savez(OUT, wj=ord_, ww=ww.astype('f4'), wnames=np.array(names))
