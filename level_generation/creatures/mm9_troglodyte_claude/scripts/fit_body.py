"""Body fit: the symmetric clean mesh -> MM9's proportions, in a symmetric bind (the mean of MM9's left and right bind directions). Each limb segment maps its own joints exactly onto MM9's lengths
(rotation + stretch, radial factor per segment), the torso by a smooth rear shift, tail on MM9's Box chain. Writes work/body1.npz (co, tri, src displacement map) and work/fit.json (target joints, left and centre)."""
import sys, json, numpy as np
sys.path.insert(0, 'scripts')
import mm9_joints
from scipy.sparse import coo_matrix
D = np.load('work/body0.npz'); P, T = D['co'].astype(float), D['tri']
J, W, par = mm9_joints.sym()
B = 'Bip02 L '
SH = np.array([0, 0, -.10])      # body shift onto MM9
S = lambda *a: np.array(a, float) + SH
src = {'sh': S(.15, .365, .01), 'el': S(.272, .125, -.172), 'wr': S(.337, -.081, -.02), 'hd': S(.345, -.125, .0), 'hip': S(.09, .13, -.35), 'kn': S(.243, -.21, -.036), 'an': S(.227, -.46, -.24), 'ball': S(.30, -.555, -.16),
       't0': S(0, .03, -.27), 't1': S(0, -.17, -.232), 't2': S(0, -.35, -.2), 't3': S(0, -.54, -.165)}
tgt = {'sh': J[B + 'UpperArm'], 'el': J[B + 'Forearm'], 'wr': J[B + 'Hand'], 'hip': J[B + 'Thigh'], 'kn': J[B + 'Calf'], 'an': J[B + 'Foot'],
       't0': J['Box01'], 't1': J['Box02'], 't2': J['Box03'], 't3': J['Box04']}
hd_dir = (J[B + 'Finger2'] - J[B + 'Hand']) if B + 'Finger2' in J else None
W_hand = W['Bip02 L Hand'][:3, 3]; W_f = W['Bip02 L Finger2'][:3, 3]; W_rh = W['Bip02 R Hand'][:3, 3]; W_rf = W['Bip02 R Finger2'][:3, 3]; X = np.array([-1, 1, 1.])
u = (W_f - W_hand) / np.linalg.norm(W_f - W_hand) + (W_rf - W_rh) * X / np.linalg.norm(W_rf - W_rh); u /= np.linalg.norm(u)
tgt['hd'] = tgt['wr'] + u * np.linalg.norm(src['hd'] - src['wr'])
tb = (J[B + 'Toe0'] - J[B + 'Foot'])
def rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
def seg(a, b, rg):
    ea, eb, ja, jb = src[a], src[b], tgt[a], tgt[b]
    u = eb - ea; L = np.linalg.norm(u); u = u / L; k = np.linalg.norm(jb - ja) / L
    R = rot(u, jb - ja)
    return dict(R=R, u=u, L=L, k=k, ea=ea, ja=ja, rg=rg)
def apply_seg(s, Q):
    q = Q - s['ea']; al = q @ s['u']; rad_ = q - np.outer(al, s['u']); t = np.clip(al / s['L'], 0, 1)
    rg = np.interp(t, *s['rg']) if isinstance(s['rg'], tuple) else s['rg']
    return s['ja'] + (np.outer(al * s['k'], s['u']) + rad_ * np.atleast_1d(rg)[:, None]) @ s['R'].T
SEGS = {}
for nm, a, b, rg in (('upper', 'sh', 'el', ((0, .5, 1), (1.0, 1.15, 1.3))), ('fore', 'el', 'wr', ((0, .35, .8, 1), (1.3, 1.45, 1.15, 1.0))), ('hand', 'wr', 'hd', 1.0), ('thigh', 'hip', 'kn', 1.08), ('calf', 'kn', 'an', 1.05), ('tail0', 't0', 't1', ((0, 1), (1.15, .78))), ('tail1', 't1', 't2', .78), ('tail2', 't2', 't3', .8)):
    SEGS[nm] = dict(seg(a, b, rg), a=a, b=b); print(nm, 'stretch', round(SEGS[nm]['k'], 3))
# foot: rigid, yaw only, the ankle on its target, sole on MM9's floor
ea, eb = src['an'], src['ball']; d0 = J[B + 'Toe0'] - J[B + 'Foot']; a = np.arctan2(d0[0], d0[2]) - np.arctan2((eb - ea)[0], (eb - ea)[2]); ca, sa = np.cos(a), np.sin(a)
Ry = np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])
print('foot yaw', np.degrees(a), 'mm9 toe', d0.round(3), 'our', (eb - ea).round(3))
SEGS['foot'] = dict(R=Ry, u=np.array([0, 1., 0]), L=1., k=1., ea=ea, ja=tgt['an'], rg=1., a='an', b='ball')
tgt['ball'] = tgt['an'] + Ry @ (eb - ea)
Q0 = P + SH
n = len(P)
def segd(Q, a, b):
    ab = b - a; t = (Q - a) @ ab / (ab @ ab); tc = np.clip(t, 0, 1)
    return np.linalg.norm(Q - a - np.outer(tc, ab), axis=1), t
names = list(SEGS); Dm = np.ones((n, len(names))) * 9
side = np.abs(Q0[:, 0])
AQ = np.c_[side, Q0[:, 1:]]        # work on the left half, mirror the map
rad = dict(upper=.11, fore=.075, hand=.3, thigh=.14, calf=.13, foot=.34, tail0=.11, tail1=.1, tail2=.08)
for i, nm in enumerate(names):
    d, t = segd(AQ, src[SEGS[nm]['a']], src[SEGS[nm]['b']])
    ok = d < rad[nm]
    if nm == 'upper': ok &= (t > -.15) & (side > .10)
    if nm == 'fore': ok &= t > -.1
    if nm == 'hand': ok &= (t > .0) & (AQ[:, 1] < -.05) & (side > .26)
    if nm == 'thigh': ok &= t > .12
    if nm == 'foot': ok &= AQ[:, 1] < -.44
    if nm == 'calf': ok &= (t < 1.05)
    if nm.startswith('tail'): ok &= side < .10
    Dm[:, i] = np.where(ok, d / rad[nm], 9)
# the leg against the arm and the tail: geometry is separate in space, the normalised distance decides
best = Dm.argmin(1); free = Dm.min(1) < 8
# torso base: smooth rear shift
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
pelvis = J['Bip01 Pelvis']; 
# sagittal radial map of the torso: the outline round C goes onto MM9's outline, top through rear to the tail root
from loadglb import load, weld
from meshlib import section
Am_, Tm_, _ = load('source/true/trog2_true.glb')
C = np.array([.20, -.33])
def outline(Pp, Tt):
    pts = np.vstack([l['pts'] for l in section(Pp, Tt, np.array([0.002, 0, 0]), np.array([1., 0, 0]))])
    q = pts[:, 1:] - C; th = np.arctan2(-q[:, 1], q[:, 0]); r = np.linalg.norm(q, axis=1)     # 0 up, +90 deg rear
    grid = np.radians(np.arange(-30, 160, 3.)); R = np.zeros(len(grid))
    for i, g in enumerate(grid):
        m = np.abs(np.angle(np.exp(1j * (th - g)))) < np.radians(7)
        R[i] = r[m].max() if m.any() else np.nan
    return grid, R
g_, Rs = outline(Q0, T); g_, Rt = outline(np.array(Am_, float), Tm_)
print('Rs', np.round(Rs, 2)); print('Rt', np.round(Rt, 2))
ratio = np.nan_to_num(Rt / Rs, nan=1.0)
ratio = np.clip(ratio, .75, 1.35)
ratio[np.degrees(g_) < 12] = 1; ratio[np.degrees(g_) > 118] = ratio[np.degrees(g_) <= 118][-1]
for _ in range(14): ratio[1:-1] = .25 * ratio[:-2] + .5 * ratio[1:-1] + .25 * ratio[2:]
print('ratio', np.round(ratio, 2))
qq = Q0[:, 1:] - C; th = np.arctan2(-qq[:, 1], qq[:, 0]); r_ = np.linalg.norm(qq, axis=1)
mv = np.interp(th, g_, ratio); Rv = np.interp(th, g_, np.nan_to_num(Rs, nan=.4))
f = ss(r_ / Rv, .15, .95)
base = Q0.copy(); base[:, 1:] = C + qq * (1 + (mv - 1) * f)[:, None]
# shoulders up onto MM9's joint, with the skin round them
gs = np.exp(-np.sum((np.c_[np.abs(Q0[:, 0]), Q0[:, 1:]] - src['sh']) ** 2, axis=1) / (2 * .12 ** 2))
sd = tgt['sh'] - src['sh']; base = base + gs[:, None] * sd * [np.nan, 1, 1] if False else base + gs[:, None] * np.c_[np.sign(Q0[:, 0]) * sd[0], np.full(n, sd[1]), np.full(n, sd[2])]
lab = np.zeros((n, len(names) + 1)); lab[np.arange(n), np.where(free, best + 1, 0)] = 1
e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr(); A.data[:] = 1
deg = np.asarray(A.sum(1)).ravel()[:, None]
for _ in range(14):
    lab = .5 * lab + .5 * (A @ lab) / deg
Q = lab[:, :1] * base
for i, nm in enumerate(names):
    q = apply_seg(SEGS[nm], AQ)
    q[:, 0] *= np.sign(Q0[:, 0] + 1e-12)
    Q = Q + lab[:, i + 1:i + 2] * q
# fair the rear torso
tm = ss(Q[:, 1], -.15, .05) * ss(-Q[:, 2], .25, .4) * (1 - ss(np.abs(Q[:, 0]), .22, .3)) * (lab[:, 0] > .3)
tm = tm[:, None]
for it in range(60):
    Q = Q + (.5 if it % 2 == 0 else -.47) * tm * ((A @ Q) / deg - Q)
print('bbox', Q.min(0).round(3), Q.max(0).round(3), 'labels', np.bincount(best[free]))
np.savez('work/body1.npz', co=Q, tri=T, src=Q0, label=np.where(free, best + 1, 0))
json.dump({'tgt': {k: v.tolist() for k, v in tgt.items()}, 'src': {k: v.tolist() for k, v in src.items()}}, open('work/fit.json', 'w'))
for k, v in tgt.items(): print(k, np.round(v, 3).tolist())
