"""Head: mirrored reduced half + procedural teeth on Meshy's sites + forked tongue. Writes work/head1.npz: co_open (Meshy's frame), co (fit frame, jaw closed by GAPE_CLOSE), tri, part (1 skin, 3 upper teeth, 4 lower teeth and fangs, 7 tongue), jawk, tongue (bone points in the fit frame)."""
import sys, numpy as np
sys.path.insert(0, 'scripts')
import headfr as H
D = np.load('work/head_half_r.npz'); P, T = D['co'].astype(float), D['tri']
on = np.where(np.abs(P[:, 0]) < 3e-5)[0]; P[on, 0] = 0
n = len(P); rem = np.arange(n, 2 * n); rem[on] = on
co = np.vstack([P, P * [-1, 1, 1]]); tri = np.vstack([T, rem[T][:, [0, 2, 1]]])
used, inv = np.unique(tri, return_inverse=True); co = co[used]; tri = inv.reshape(-1, 3); part = np.ones(len(co), int)
S = np.load('work/head_sites.npz')['s']
def tooth(base, ax, L, w, curve=0., M=4):
    ax = ax / np.linalg.norm(ax); t = np.cross(ax, [0, 0, 1.]); t /= np.linalg.norm(t); u = np.cross(ax, t)
    th = np.linspace(0, 2 * np.pi, M, endpoint=False) + np.pi / 4
    V = []
    prof = ((0, 1.), (.5, .62)) if M == 4 else ((0, 1.), (.3, .85), (.6, .58), (.82, .3))
    for f, r in prof:
        V.append(base + ax * L * f + np.array([0, 0, curve]) * f * f + r * w * (np.cos(th)[:, None] * t + np.sin(th)[:, None] * u))
    V = np.vstack(V + [(base + ax * L + np.array([0, 0, curve]))[None]]); F = []
    for k in range(len(prof) - 1):
        for i in range(M):
            j = (i + 1) % M; a, b, c, e = k * M + i, k * M + j, (k + 1) * M + j, (k + 1) * M + i
            F += [[a, c, b], [a, e, c]]
    tip = len(V) - 1; k = len(prof) - 1
    for i in range(M): F.append([k * M + i, tip, k * M + (i + 1) % M])
    F = np.array(F)
    # outward test
    ce = V.mean(0); f0 = V[F[0]]; 
    if np.cross(f0[1] - f0[0], f0[2] - f0[0]) @ (f0.mean(0) - ce) < 0: F = F[:, [0, 2, 1]]
    return V, F
Vs = [co]; Fs = [tri]; parts = [part]; nv = len(co)
for s in S:
    ce, ax, ext, up = s[:3], s[3:6], s[6], s[7] > .5
    fang = ext > .05
    L = ext * 1.15 if fang else ext * 1.5; w = ext * .22 if fang else ext * .36; base = ce - ax * (ext * .58 if fang else ext * .62)
    for sg in (1, -1):
        v, f = tooth(base * [sg, 1, 1], ax * [sg, 1, 1], L, w, curve=-.012 if fang else 0, M=6 if fang else 4)
        Vs.append(v); Fs.append(f + nv); nv += len(v); parts.append(np.full(len(v), 3 if up else 4))
# tongue: lies on the floor pad, forked near the tip (Meshy frame). Floor line from the centre section, fit frame points mapped back
Cf = np.array([[0, .668, .17], [0, .652, .23], [0, .626, .29], [0, .603, .345], [0, .588, .395]])     # floor + 1.2 cm
Cm = H.Fi(Cf); 
def ring(c, t, w, h, M=6):
    th = np.linspace(0, 2 * np.pi, M, endpoint=False); up = np.array([0, 1., .3]); up /= np.linalg.norm(up)
    return c + np.outer(np.cos(th) * w, [1, 0, 0]) + np.outer(np.sin(th) * h, up)
sts = [(0, .030, .011), (.25, .032, .012), (.5, .030, .012), (.7, .024, .010)]
Ct = lambda u: np.array([np.interp(u, np.linspace(0, 1, len(Cm)), Cm[:, k]) for k in range(3)])
V = [ring(Ct(u), u, w, h) for u, w, h in sts]; F = []
M = 6
for k in range(len(sts) - 1):
    for i in range(M):
        j = (i + 1) % M; a, b, c, e = k * M + i, k * M + j, (k + 1) * M + j, (k + 1) * M + i
        F += [[a, c, b], [a, e, c]]
base = (len(sts) - 1) * M
# fork: two tips from the last ring
for sg in (1, -1):
    t1 = Ct(.86) + np.array([sg * .017, 0, 0]); t2 = Ct(1.03) + np.array([sg * .03, .006, 0])
    r1 = ring(t1, 0, .011, .007); tipi = len(np.vstack(V)) + 6
    b1 = len(np.vstack(V)); V.append(r1); V.append(t2[None])
    for i in range(M):
        j = (i + 1) % M
        F += [[b1 + i, tipi, b1 + j]]
        # side of the last ring into this ring: half of the ring only
    idx = [0, 1, 5] if sg > 0 else [2, 3, 4]
    for q, (i, j) in enumerate(zip([5, 0, 1] if sg > 0 else [2, 3, 4], [0, 1, 2] if sg > 0 else [3, 4, 5])):
        a, b = base + i, base + j; c, e = b1 + j, b1 + i
        F += [[a, c, b], [a, e, c]]
    for i, j in ([(2, 3), (3, 4), (4, 5), (5, 0)] if False else []): pass
# closing webs of the fork: the middle of the last ring joined over x=0 on both faces
F += [[base + 1, base + 2, base + 4], [base + 1, base + 4, base + 5]]
Vt = np.vstack(V); Ft = np.array(F)
ce = Ct(.5); 
Vs.append(Vt); Fs.append(Ft + nv); nv += len(Vt); parts.append(np.full(len(Vt), 7))
co = np.vstack(Vs); tri = np.vstack(Fs); part = np.concatenate(parts)
print('head', len(co), len(tri), {int(k): int((part[tri[:, 0]] == k).sum()) for k in np.unique(part)})
fit0 = H.F(co)
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
# jaw weight: plane through the hinge, descending forward; fades out toward the neck
nb = np.array([0, np.cos(H.MID_SLOPE), np.sin(H.MID_SLOPE)])
d = (fit0 - H.HINGE) @ nb
k = 1 - ss(d, -.028, .012)
back = ss(fit0[:, 2], .06, .19)
k = k * back
k[part == 3] = 0; k[part == 4] = 1; k[part == 7] = 1
th = np.radians(H.GAPE_CLOSE) * k
rel = fit0 - H.HINGE; y, z = rel[:, 1], rel[:, 2]
cl = fit0.copy(); cl[:, 1] = H.HINGE[1] + y * np.cos(th) + z * np.sin(th); cl[:, 2] = H.HINGE[2] - y * np.sin(th) + z * np.cos(th)
print('closed tips lower', cl[part == 4].max(0).round(3), 'bbox', cl.min(0).round(3), cl.max(0).round(3))
# tongue bone points in the closed fit frame
tb = H.F(np.array([Ct(u) for u in (0, .33, .66, 1.)]))
kk = np.ones(4); rel = tb - H.HINGE; a = np.radians(H.GAPE_CLOSE); y, z = rel[:, 1], rel[:, 2]; tb[:, 1] = H.HINGE[1] + y * np.cos(a) + z * np.sin(a); tb[:, 2] = H.HINGE[2] - y * np.sin(a) + z * np.cos(a)
np.savez('work/head1.npz', co_open=co, co=cl, tri=tri, part=part, jawk=k, tongue=tb)
print('tongue', tb.round(3).tolist())
