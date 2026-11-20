"""Head: mirrored reduced half + procedural teeth (MM9: pointed upper, big blunt lower) on Meshy's tooth sites + eyes. Writes work/head1.npz: co_open (Meshy frame, x flipped), co (fit frame, jaw closed to GAPE), tri, part (1 skin, 3 upper teeth, 4 lower teeth, 6 eyes), jawk."""
import sys, numpy as np
sys.path.insert(0, 'scripts')
from scipy.sparse import coo_matrix
HM = np.array([0, -.07, -.13]); A = np.radians(25.8); S = .53
c_, s_ = np.cos(A), np.sin(A); RX = np.array([[1, 0, 0], [0, c_, -s_], [0, s_, c_]]); HT = np.array([0, .285, .023])
GAPE0 = 46.; GAPE = 12.
D = np.load('work/head_half_r.npz'); P, T = D['co'].astype(float), D['tri']
on = np.where(np.abs(P[:, 0]) < 3e-5)[0]; P[on, 0] = 0
n = len(P); rem = np.arange(n, 2 * n); rem[on] = on
co = np.vstack([P, P * [-1, 1, 1]]); tri = np.vstack([T, rem[T][:, [0, 2, 1]]])
used, inv = np.unique(tri, return_inverse=True); co = co[used]; tri = inv.reshape(-1, 3); part = np.ones(len(co), int)
B = np.load('work/head_bits.npz'); Pb, Tb, lb = B['P'], B['T'], B['l']
def tooth(base, ax, tang, L, w, d, blunt):
    """rings round the axis; returns verts, tris. Axis from the root to the tip, tang along the row."""
    ax = ax / np.linalg.norm(ax); t = tang - ax * (tang @ ax); t /= np.linalg.norm(t); u = np.cross(ax, t)
    M = 6; th = np.linspace(0, 2 * np.pi, M, endpoint=False)
    prof = ((0, 1.), (.55, 1.05), (.85, .8)) if blunt else ((0, 1.), (.4, .85), (.75, .42))
    V = []
    for f, r in prof:
        V.append(base + ax * L * f + r * (np.cos(th)[:, None] * t * w + np.sin(th)[:, None] * u * d))
    V = np.vstack(V + [(base + ax * L)[None]]); F = []
    for k in range(len(prof) - 1):
        for i in range(M):
            j = (i + 1) % M; a, b, c, e = k * M + i, k * M + j, (k + 1) * M + j, (k + 1) * M + i
            F += [[a, b, c], [a, c, e]]
    tip = len(V) - 1; k = len(prof) - 1
    for i in range(M): F.append([k * M + i, k * M + (i + 1) % M, tip])
    return V, np.array(F)
UP = [18, 16, 14, 12, 9, 7, 4]; LO = [17, 15, 13, 11, 10, 8, 6, 5, 3, 2]
def row(ids, up):
    q = []
    for c in ids:
        Q = Pb[lb == c]; cen = Q.mean(0)
        U, s, Vt = np.linalg.svd(Q - cen); ax = Vt[0]
        if (ax[1] > 0) == up: ax = -ax          # root -> tip: upper teeth down, lower up
        q.append((cen, ax))
    return q
Vs = [co]; Fs = [tri]; parts = [part]; nv = len(co)
for ids, up in ((UP, True), (LO, False)):
    r = row(ids, up); pts = np.array([x[0] for x in r])
    for i, (cen, ax) in enumerate(r):
        tang = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        k = 1 - .35 * i / (len(r) - 1)
        L = (.075 if up else .07) * (k if up else 1 - .25 * i / (len(r) - 1)); w = (.021 if up else .024) * (.8 + .2 * k); d = .017 if up else .019
        base = cen - ax * .045
        if not up and i == 0: base = base * [.62, 1, 1]
        for sg in (1, -1):
            v, f = tooth(base * [sg, 1, 1], ax * [sg, 1, 1], tang * [sg, 1, 1], L, w, d, not up)
            if sg < 0: f = f[:, [0, 2, 1]]
            Vs.append(v); Fs.append(f + nv); nv += len(v); parts.append(np.full(len(v), 3 if up else 4))
# eyes: Meshy's lid and ball, right-hand site, mirrored; thinned by a voxel-free vertex cluster
E_ = Pb[lb == 1]; Eid = np.where(lb == 1)[0]; rem2 = -np.ones(len(Pb), int); rem2[Eid] = np.arange(len(Eid)); Te = rem2[Tb[(lb == 1)[Tb[:, 0]]]]
np.savez('work/eye_half.npz', co=E_, tri=Te, protect=np.zeros(len(E_)))
if len(sys.argv) > 1:
    D2 = np.load(sys.argv[1]); Ev, Ef = D2['co'], D2['tri']
    for sg in (1, -1):
        f = Ef if sg > 0 else Ef[:, [0, 2, 1]]
        Vs.append(Ev * [sg, 1, 1]); Fs.append(f + nv); nv += len(Ev); parts.append(np.full(len(Ev), 6))
co = np.vstack(Vs); tri = np.vstack(Fs); part = np.concatenate(parts)
print('head', len(co), len(tri), {int(k): int((part[tri[:, 0]] == k).sum()) for k in np.unique(part)})
# jaw weight: the bisecting plane through the hinge, fading out toward the neck ring
ang = np.radians((25.8 - 20.2) / 2)      # mid plane of the gape, from +z toward +y
nb = np.array([0, np.cos(ang), -np.sin(ang)])
d = (co - HM) @ nb
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
k = 1 - ss(d, -.035, .035)
back = ss(co[:, 2], -.31, -.12)              # neck ring (z=-.318) keeps to the head
k = k * back
# tongue and floor stay on the jaw behind the hinge valley; the valley splits on the plane
k[part == 3] = 0; k[part == 4] = 1; k[part == 6] = 0
# the rear rim of the jaw: decimated triangles span the bisecting band, so k steps across them and the edge frays when the jaw opens (user, Hit frame 27). Smooth k along the skin behind the hinge
sk = part == 1; e_ = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]); N_ = len(co)
A_ = coo_matrix((np.ones(len(e_) * 2), (np.r_[e_[:, 0], e_[:, 1]], np.r_[e_[:, 1], e_[:, 0]])), shape=(N_, N_)).tocsr(); A_.data[:] = 1
dg = np.maximum(np.asarray(A_.sum(1)).ravel(), 1); rear = sk & (co[:, 2] < .02)
for _ in range(10):
    q = (A_ @ k) / dg; k[rear] = .5 * k[rear] + .5 * q[rear]
# closed: each vertex rotates by k x theta about the hinge (arc, not a chord)
th = np.radians(GAPE0 - GAPE) * k
rel = co - HM; y, z = rel[:, 1], rel[:, 2]
cl = co.copy(); cl[:, 1] = HM[1] + y * np.cos(th) + z * np.sin(th); cl[:, 2] = HM[2] - y * np.sin(th) + z * np.cos(th)
fit = (cl - HM) @ RX.T * S + HT
print('closed tips: lower', fit[part == 4].max(0).round(3), 'upper', fit[part == 3].min(0).round(3), 'bbox', fit.min(0).round(3), fit.max(0).round(3))
np.savez('work/head1.npz', co_open=co, co=fit, tri=tri, part=part, jawk=k, theta=np.radians(GAPE0 - GAPE))
