"""Body weights by part from the heat weights (from mm9_evilsorcerer_claude/scripts/weights.py).
Args: <asm npz> <heat npz> <rig json> <labels npy> <out npz> -> W (n x bones), names"""
import sys, json, os
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from rig_bones import FINGERS, half_pairs
J_, H_, R_, L_, OUT = sys.argv[1:6]
D = np.load(J_); co, tri, comp = D['co'], D['tri'], D['comp']; pn = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(pn)}
H = np.load(H_); W = H['W'].astype(np.float64); names = [str(x) for x in H['names']]
extra = [n for n in ('Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck', 'Bip01 Head',
                     'Bip01 L Clavicle', 'Bip01 R Clavicle') if n not in names]
names = names + extra; W = np.c_[W, np.zeros((len(W), len(extra)))]
ix = {n: i for i, n in enumerate(names)}
labels = np.load(L_)
RJ = json.load(open(R_)); JJ = RJ['joints']
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
def only(mask, *bones):
    keep = np.zeros(W.shape[1]); keep[[ix[b] for b in bones]] = 1
    W[mask] *= keep; s = W[mask].sum(1); ids = np.where(mask)[0]
    W[ids[s < 1e-6], ix[bones[0]]] = 1
def rigid(mask, b): W[mask] = 0; W[mask, ix[b]] = 1
skin = P('body')
fingers = labels > 0
smooth(skin & ~fingers, int(os.environ.get('PASSES', '4')))
sj = np.array(JJ['Bip01 L UpperArm'])
zone = (np.minimum(np.linalg.norm(co - sj, axis=1), np.linalg.norm(co - sj * [-1, 1, 1], axis=1)) < 0.13) & skin
smooth(zone, int(os.environ.get('SHPASS', '6')))
# hands
for lab, f in enumerate(FINGERS, 1):
    for s, sgn in (('L', -1), ('R', 1)):
        vs = (labels == lab) & (co[:, 0] * sgn > 0)
        only(vs, f'Bip01 {s} Hand', *[f'Bip01 {s} {f}{k}' for k in (1, 2, 3)])
for s, sgn in (('L', -1), ('R', 1)):
    wr = np.array(JJ[f'Bip01 {s} Hand']); el = np.array(JJ[f'Bip01 {s} Forearm']); ax = (wr - el) / np.linalg.norm(wr - el)
    t = (co - wr) @ ax
    handzone = skin & (labels == 0) & (co[:, 0] * sgn > 0) & (t > 0.01) & (np.linalg.norm(co - wr, axis=1) < 0.2)
    allow = [f'Bip01 {s} Hand'] + [f'Bip01 {s} {f}1' for f in FINGERS] + [f'Bip01 {s} Thumb2']
    only(handzone, *allow)
    # wrist: a short blend forearm -> hand
    wz = skin & (labels == 0) & (co[:, 0] * sgn > 0) & (np.abs(t) <= 0.01 + 1e-9) & (np.linalg.norm(co - wr, axis=1) < 0.08)
    u = ss(t[wz], -0.03, 0.01)
    W[wz] = 0; W[wz, ix[f'Bip01 {s} Forearm']] = 1 - u; W[wz, ix[f'Bip01 {s} Hand']] = u
    # legs below the knee: calf/foot/toe only; foot and heel
    only(skin & (co[:, 0] * sgn > 0.03) & (co[:, 2] < -0.3), f'Bip01 {s} Calf', f'Bip01 {s} Foot', f'Bip01 {s} Toe0', f'Bip01 {s} Thigh')
# knee and elbow: a tight blend round the joint
for s, sgn in (('L', -1), ('R', 1)):
    for pr, a, b, c, rad in ((f'Bip01 {s} ', 'Thigh', 'Calf', 'Foot', 0.07), (f'Bip01 {s} ', 'UpperArm', 'Forearm', 'Hand', 0.06)):
        ja, jb, jc = [np.array(JJ[pr + k]) for k in (a, b, c)]
        ax = (jc - ja) / np.linalg.norm(jc - ja)
        t = (co - jb) @ ax
        sel = skin & (co[:, 0] * sgn > 0) & ((W[:, ix[pr + a]] + W[:, ix[pr + b]]) > 0.2) & (np.abs(t) < 0.25)
        tot = W[sel, ix[pr + a]] + W[sel, ix[pr + b]]
        bl = ss(t[sel], -rad, rad)
        W[sel, ix[pr + a]] = tot * (1 - bl); W[sel, ix[pr + b]] = tot * bl
    # foot: ankle blend calf -> foot, toes
    fa = np.array(JJ[f'Bip01 {s} Foot']); toe = np.array(JJ[f'Bip01 {s} Toe0'])
    fz = skin & (co[:, 0] * sgn > 0.03) & (co[:, 2] < -0.45)
    u = ss(-(co[fz, 2] - fa[2]), -0.04, 0.03)
    tw = ss(-(co[fz, 1] - toe[1]), -0.01, 0.025)
    W[fz] = 0; W[fz, ix[f'Bip01 {s} Calf']] = 1 - u; W[fz, ix[f'Bip01 {s} Foot']] = u * (1 - tw); W[fz, ix[f'Bip01 {s} Toe0']] = u * tw
# head: rigid above the jaw line (higher behind), neck blends into the head
jaw = co[:, 2] - 0.20 * co[:, 1]
u = ss(jaw, 0.758, 0.792)
hz = skin & (co[:, 2] > 0.70) & (np.abs(co[:, 0]) < 0.13)
neckw = W[hz].copy()
W[hz] = neckw * (1 - u[hz])[:, None]; W[hz, ix['Bip01 Head']] += u[hz]
for part in ('eyes', 'mouth', 'ears', 'horns', 'fringe'):
    rigid(P(part), 'Bip01 Head')
# hair: head above the ears, then towards Neck and Spine3 down the back of the hair (it hangs from the skull)
hv = P('hair'); z = co[:, 2]
a = ss(z, 0.70, 0.80)          # 1 head
W[hv] = 0
W[hv, ix['Bip01 Head']] = a[hv]
W[hv, ix['Bip01 Neck']] = (1 - a[hv]) * (1 - ss(z[hv], 0.6, 0.70)) * 0.5 + (1 - a[hv]) * ss(z[hv], 0.6, 0.70)
W[hv, ix['Bip01 Spine3']] = (1 - a[hv]) * (1 - ss(z[hv], 0.6, 0.70)) * 0.5
smooth(hv, 6)
# parts on the torso: nearest body vertex weights
src = np.where(skin & (labels == 0))[0]; kd = cKDTree(co[src])
for nm, passes in (('belt', 12), ('emblem', 6), ('spikes', 0)):
    q = np.where(P(nm))[0]
    if not len(q): continue
    W[q] = W[src[kd.query(co[q])[1]]]
    if passes: smooth(P(nm), passes)
for nm in ('spikes',):          # emblem keeps the weights of the body under it (a rigid mean drifted 2 cm off the groin in FallDown)
    for sgn in ((-1, 1) if nm == 'spikes' else (0,)):
        sel = P(nm) & ((co[:, 0] * sgn > 0) if sgn else True)
        if sel.any(): W[sel] = W[sel].mean(0)          # rigid plates
only(P('belt'), 'Bip01 Spine', 'Bip01 Pelvis', 'Bip01 Spine1', 'Bip01 L Thigh', 'Bip01 R Thigh')
smooth(P('belt'), 20)
# half joints
pairs = half_pairs()
names = names + [h for h, _, _, _ in pairs]
W = np.c_[W, np.zeros((len(W), len(pairs)))]; ix = {n: i for i, n in enumerate(names)}
rigidparts = P('eyes') | P('mouth') | P('horns') | P('spikes') | fingers
for h, c, _, ps in pairs:
    ic = ix[c]; ip = [ix[x] for x in ps]
    a_ = W[:, ip].sum(1); b_ = W[:, ic]; m_ = np.minimum(a_, b_)
    sel = (m_ > 1e-4) & ~rigidparts
    W[sel, ix[h]] = 2 * m_[sel]; W[sel, ic] -= m_[sel]
    W[np.ix_(np.where(sel)[0], ip)] *= (1 - m_[sel] / a_[sel])[:, None]
W /= np.maximum(W.sum(1, keepdims=True), 1e-12)
print('unweighted', int((W.sum(1) < 1e-5).sum()))
np.savez(OUT, W=W.astype('f4'), names=np.array(names))
