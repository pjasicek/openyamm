"""Body fit, half mesh x>=0 (work/half0.npz) -> work/half1.npz: MM9's joints, MM9's exact bone lengths and bind directions (the bind is symmetric). Each limb segment maps its joints onto MM9's (rotation + stretch + radial profile), the torso leans forward
by a shear, the tail is mapped by arc length onto the Box chain. Shells (bracer, greave, pauldron) take their limb's map as one rigid piece. Writes co, tri, comp, src, label. Also work/fit.json."""
import sys, json, numpy as np
sys.path.insert(0, 'scripts')
import mm9_joints
from scipy.sparse import coo_matrix
D = np.load(sys.argv[1] if len(sys.argv)>1 else 'work/half0r.npz'); P, T, comp = D['co'].astype(float), D['tri'], D['comp']
W, par, _ = mm9_joints.rest(); J = {k: v[:3, 3].copy() for k, v in W.items()}
B = 'Bip01 L '
S = lambda *a: np.array(a, float)
src = {'sh': S(.225, .56, -.06), 'el': S(.385, .275, -.07), 'wr': S(.572, .055, -.04), 'hd': S(.655, -.03, -.03), 'hip': S(.125, .03, -.03), 'kn': S(.228, -.385, .005), 'an': S(.245, -.74, -.09)}
tgt = {'sh': J[B + 'UpperArm'], 'el': J[B + 'Forearm'], 'wr': J[B + 'Hand'], 'hip': J[B + 'Thigh'], 'kn': J[B + 'Calf'], 'an': J[B + 'Foot']}
tgt['hd'] = tgt['wr'] + (J[B + 'Finger1'] - tgt['wr']) / np.linalg.norm(J[B + 'Finger1'] - tgt['wr']) * np.linalg.norm(src['hd'] - src['wr'])
def rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
def seg(a, b, rg):
    ea, eb, ja, jb = src[a], src[b], tgt[a], tgt[b]
    u = eb - ea; L = np.linalg.norm(u); u = u / L; k = np.linalg.norm(jb - ja) / L
    return dict(R=rot(u, jb - ja), u=u, L=L, k=k, ea=ea, ja=ja, rg=rg, a=a, b=b)
def apply_seg(s, Q):
    q = Q - s['ea']; al = q @ s['u']; rad_ = q - np.outer(al, s['u']); t = np.clip(al / s['L'], 0, 1)
    rg = np.interp(t, *s['rg']) if isinstance(s['rg'], tuple) else s['rg']
    return s['ja'] + (((np.outer(al * s['k'], s['u']) + rad_ * np.atleast_1d(rg)[:, None])) @ s['R'].T)
SEGS = {n: seg(a, b, rg) for n, a, b, rg in (('upper', 'sh', 'el', 1.0), ('fore', 'el', 'wr', .92), ('hand', 'wr', 'hd', 1.0), ('thigh', 'hip', 'kn', 1.0), ('calf', 'kn', 'an', 1.0))}
for k, v in SEGS.items(): print(k, 'stretch', round(v['k'], 3), 'turn', round(np.degrees(np.arccos(np.clip((np.trace(v['R']) - 1) / 2, -1, 1))), 1))
# foot: rigid, ankle on target, sole on the floor
SEGS['foot'] = dict(R=np.eye(3), u=np.array([0, 1., 0]), L=1., k=1., ea=src['an'], ja=tgt['an'] + np.array([0, src['an'][1] - tgt['an'][1] + 0 * 1, 0]) * 1, rg=1., a='an', b='an')
SEGS['foot']['ja'] = np.array([tgt['an'][0], src['an'][1], tgt['an'][2]])      # the sole stays on the floor: the ankle's height differs by 1.7 cm, taken by the calf's top of the foot
tgt['foot'] = SEGS['foot']['ja']
# torso: forward shear with height
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def torso(Q):
    q = Q.copy(); q[:, 2] += .06 * ss(Q[:, 1], .05, .45); return q
# tail by arc length
tail_src = np.array([[0, .03, -.16], [0, -.02, -.20], [0, -.091, -.30], [0, -.156, -.40], [0, -.218, -.50], [0, -.278, -.60], [0, -.339, -.70], [0, -.393, -.80], [0, -.439, -.90], [0, -.475, -1.0], [0, -.506, -1.1], [0, -.534, -1.2], [0, -.559, -1.3], [0, -.60, -1.46]])
tail_tgt = np.array([J['Box03'], J['Box04'], J['Box05'], np.array([0, -.30, -.62])])
def arclen(x): return np.r_[0, np.cumsum(np.linalg.norm(np.diff(x, axis=0), axis=1))]
ss_, st_ = arclen(tail_src), arclen(tail_tgt); print('tail length', ss_[-1], st_[-1])
def tail_map(Q):
    # nearest polyline param
    a, b = tail_src[:-1], tail_src[1:]; ab = b - a; t = np.clip(((Q[:, None] - a[None]) * ab[None]).sum(2) / (ab * ab).sum(1), 0, 1)
    pr = a[None] + t[..., None] * ab[None]; d = np.linalg.norm(Q[:, None] - pr, axis=2); i = d.argmin(1); r = np.arange(len(Q))
    s = (ss_[i] + t[r, i] * np.linalg.norm(ab, axis=1)[i]) / ss_[-1]
    uu = ab[i] / np.linalg.norm(ab[i], axis=1, keepdims=True); off = Q - pr[r, i]
    # frame: x stays, v = u x x
    tg = np.c_[[np.interp(s * st_[-1], st_, tail_tgt[:, k]) for k in range(3)]].T
    k = np.searchsorted(st_, s * st_[-1]).clip(1, len(st_) - 1); ut = tail_tgt[k] - tail_tgt[k - 1]; ut /= np.linalg.norm(ut, axis=1, keepdims=True)
    v0 = np.cross(uu, [1., 0, 0]); v1 = np.cross(ut, [1., 0, 0])
    prof = np.interp(s, [0, .25, 1], [1.0, .86, .8])
    return tg + (np.outer(off[:, 0], [1, 0, 0]) + np.outer((off * v0).sum(1), [1, 0, 0]) * 0 + v1 * (off * v0).sum(1, keepdims=True)) * prof[:, None], d[r, i], s
n = len(P); names = ['upper', 'fore', 'hand', 'thigh', 'calf', 'foot']
Dm = np.ones((n, len(names) + 1)) * 9
def segd(Q, a, b):
    ab = b - a; t = (Q - a) @ ab / (ab @ ab); tc = np.clip(t, 0, 1)
    return np.linalg.norm(Q - a - np.outer(tc, ab), axis=1), t
rad = dict(upper=.15, fore=.13, hand=.32, thigh=.20, calf=.16, foot=.40)
for i, nm in enumerate(names):
    s = SEGS[nm]
    b_ = src[s['b']] if nm != 'foot' else src['an'] + [0, -.2, .1]
    d, t = segd(P, src[s['a']], b_)
    ok = d < rad[nm]
    if nm == 'upper': ok &= (t > -.1) & (P[:, 0] > .17)
    if nm == 'fore': ok &= t > -.05
    if nm == 'hand': ok &= (t > .0) & (P[:, 0] > .45) & (P[:, 1] < .15)
    if nm == 'thigh': ok &= (t > .08) & (P[:, 1] < .05)
    if nm == 'calf': ok &= t < 1.0
    if nm == 'foot': ok &= P[:, 1] < -.725
    Dm[:, i] = np.where(ok, d / rad[nm], 9)
Qt, dt, st = tail_map(P)
tail = (P[:, 0] < .13) & (P[:, 2] < -.16) & (P[:, 1] < .06) & (dt < .15)
Dm[:, 6] = np.where(tail, .01, 9)
best = Dm.argmin(1); free = Dm.min(1) < 8
lab = np.zeros((n, 8)); lab[np.arange(n), np.where(free, best + 1, 0)] = 1
e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr(); A.data[:] = 1
deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)[:, None]
# main hide comp only is smoothed; shells take one label
sz = np.bincount(comp); main = int(sz.argmax())
for _ in range(10): lab = .5 * lab + .5 * (A @ lab) / deg
base = torso(P)
sd = tgt['sh'] - torso(src['sh'][None])[0]
hdg = np.exp(-np.sum((P - src['sh']) ** 2, axis=1) / (2 * .13 ** 2)); base = base + hdg[:, None] * sd
Q = lab[:, :1] * base
out = {nm: apply_seg(SEGS[nm], P) for nm in names}; out['tail'] = Qt
for i, nm in enumerate(names + ['tail']):
    Q = Q + lab[:, i + 1:i + 2] * out[nm]
# shells rigid with one limb
def pick(c):
    q = P[comp == c]; ce = q.mean(0)
    if q[:, 1].mean() > .39 and ce[0] > .13 and q[:, 1].max() > .5 or (ce[0] > .2 and ce[1] > .45): return 'pauldron'
    if ce[0] > .35 and ce[1] > .02 and ce[1] < .3: return 'fore'
    if ce[1] < -.4: return 'calf'
    return None
sh_map = {}
RU = SEGS['upper']['R']
for c in np.unique(comp):
    if c == main: continue
    p = pick(c); sh_map[int(c)] = p; m = comp == c
    if p == 'pauldron':
        q = (P[m] - src['sh']) @ rot(np.array([1, -1.2, 0]), np.array([1, -1.0, 0])).T + tgt['sh'] + [0.0, .0, 0]; Q[m] = q      # most of the arm's turn is at the socket
    elif p:
        c0 = apply_seg(SEGS[p], P[m].mean(0)[None])[0]; Q[m] = c0 + (P[m] - P[m].mean(0)) @ SEGS[p]['R'].T
    else: Q[m] = base[m]
print('shells', sh_map)
on = np.abs(P[:, 0]) < 1e-9; Q[on, 0] = 0
print('bbox', Q.min(0).round(3), Q.max(0).round(3), 'labels', np.bincount(best[free]))
np.savez('work/half1.npz', co=Q, tri=T, comp=comp, src=P, label=np.where(free, best + 1, 0))
json.dump({'tgt': {k: np.asarray(v).tolist() for k, v in tgt.items()}, 'src': {k: v.tolist() for k, v in src.items()}}, open('work/fit.json', 'w'))
