"""Head-only Smart Topology -> half clean (work/head_half.npz), with the back cut at the neck plane, threads gone, cap removed. Frame: Meshy's (head tipped back 25.8 deg, jaw open). x>0 half kept after flipping: Meshy's x<0 side is clean.
Teeth roots and eye written to work/head_bits.npz."""
import sys, numpy as np
sys.path.insert(0, 'scripts')
from loadglb import *
from clip import clip
P, T, _ = load('meshy/head_v1/model_urls_glb.glb'); P, T, _, _ = weld(P, T)
X0 = -.003; P[:, 0] -= X0; P[:, 0] *= -1; T = T[:, [0, 2, 1]]        # the clean side at x>0
nc, l = comps(len(P), T); sz = np.bincount(l); main = int(np.argmax(sz))
print('main', sz[main])
bits = []
for c in range(nc):
    if c == main: continue
    Q = P[l == c]; bits.append((c, Q.mean(0), np.ptp(Q, 0), sz[c]))
# frame constants
HM = np.array([0, -.07, -.13]); A = np.radians(25.8); S = .53
c_, s_ = np.cos(A), np.sin(A); RX = np.array([[1, 0, 0], [0, c_, -s_], [0, s_, c_]]); HT = np.array([0, .285, .023])
def tofit(p): return (p - HM) @ RX.T * S + HT
def fromfit(p): return HM + ((p - HT) / S) @ RX
pi0 = np.array([0, .352, -.055]); nn = np.array([0, -np.sin(A), np.cos(A)])
pm = fromfit(pi0); nm = nn @ RX
print('plane in meshy frame', pm.round(3), nm.round(3))
Tm = T[(l == main)[T[:, 0]]]
cen = P[Tm].mean(1)
Lf = P[Tm]; Lm = np.max([np.linalg.norm(Lf[:, 0] - Lf[:, 1], axis=1), np.linalg.norm(Lf[:, 1] - Lf[:, 2], axis=1), np.linalg.norm(Lf[:, 2] - Lf[:, 0], axis=1)], axis=0)
Ar = np.linalg.norm(np.cross(Lf[:, 1] - Lf[:, 0], Lf[:, 2] - Lf[:, 0]), axis=1) / 2
thin = (Lm > .05) & (Ar / Lm ** 2 < .04)
print('thin faces', int(thin.sum()))
keep = (cen[:, 0] > 0) & ~thin
Tm = Tm[keep]
P, Tm, _, ring_new = clip(P, Tm, pm, nm)
print('clipped ring', len(ring_new), 'verts', len(P))
l_old = l; l = np.r_[l, np.full(len(P) - len(l), main)]
def boundary(T):
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1); u, c = np.unique(e, axis=0, return_counts=True); return u[c == 1]
# largest connected piece only (scraps of teeth roots)
n_ = len(P); nc2, l2 = comps(n_, Tm); s2 = np.bincount(l2[np.unique(Tm)], minlength=nc2); big = int(np.argmax(s2)); print('pieces', np.sort(s2)[-6:])
Tm = Tm[l2[Tm[:, 0]] == big]
b = boundary(Tm)
Bv = np.unique(b); print('boundary verts', len(Bv))
seam = Bv[np.abs(P[Bv, 0]) < .02]; P[seam, 0] = 0
ring = Bv[np.abs((P[Bv] - pm) @ nm) < 1e-6]
print('seam', len(seam), 'ring', len(ring), 'others', len(np.setdiff1d(Bv, np.r_[seam, ring])), P[np.setdiff1d(Bv, np.r_[seam, ring])].round(2)[:12].tolist())
used, inv = np.unique(Tm, return_inverse=True); co = P[used]; tri = inv.reshape(-1, 3)
rem = -np.ones(len(P), int); rem[used] = np.arange(len(used))
pr = np.zeros(len(co)); pr[rem[seam]] = 1; pr[rem[ring]] = 1
# the rim of the lips and the eye sockets keep their shape
strip = np.zeros(len(co), bool)
# lips denser: rim of the mouth, eyes' socket
lip = (co[:, 2] > -.1) & (np.abs(co[:, 1] - .03 - .12 * 0) < 2)
print('half', len(co), len(tri))
np.savez('work/head_half.npz', co=co, tri=tri, protect=pr)
np.savez('work/head_bits.npz', ids=np.array([b_[0] for b_ in bits]), cen=np.array([b_[1] for b_ in bits]), ext=np.array([b_[2] for b_ in bits]), sz=np.array([b_[3] for b_ in bits]), P=P[:len(l_old)], T=T, l=l_old)
for b_ in sorted(bits, key=lambda q: -q[3]): print(b_[0], b_[3], np.round(b_[1], 3).tolist(), np.round(b_[2], 3).tolist())
