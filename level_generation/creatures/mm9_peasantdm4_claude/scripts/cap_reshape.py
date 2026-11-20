"""Reshape the cap's crown toward MM9's tall, flat-topped soft skullcap (coordinator review 2026-11-02: ours read as a round
domed metal helmet). Positions only (UVs, paint and the projected medallion follow the faces). Cap = the head-face loose part
holding the highest head vertex. Per azimuth (24 sectors about the cap centre CX, CY): band top zb = the sector's lowest cap
vertex + BAND; R0 = mean radius of the cap vertices within 5 mm of zb. A Taubin-smoothed copy of the cap (SMOOTH passes,
its lowest ring fixed) stands for the dome; each vertex moves along its own ray from (CX, CY, zb) onto the target, a
frustum r = R0 - TAPER h with a flat top at h = HTOP (the old crown height + RAISE), and the vertex takes that displacement
(times its distance ratio to the smooth dome: Meshy's folds kept), weighted by smoothstep(h, 0, 1.2 cm) so the band does not move.
Args (Blender): <in blend> <out blend> [raise 0.02] [taper 0.2] [band 0.035] [cx,cy 0.0,0.055]"""
import bpy, bmesh, sys, math, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
RAISE = float(a[2]) if len(a) > 2 else 0.02; TAPER = float(a[3]) if len(a) > 3 else 0.2
BAND = float(a[4]) if len(a) > 4 else 0.035
CX, CY = (float(t) for t in (a[5] if len(a) > 5 else '0.0,0.055').split(','))
SMOOTH, NSEC = 40, 24
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
hl = bm.faces.layers.int.get('head')
hv = [v for f in bm.faces if f[hl] == 1 for v in f.verts]
top = max(hv, key=lambda v: v.co.z)
part = set(); st = [top]
while st:
    v = st.pop()
    if v in part: continue
    part.add(v); st += [e.other_vert(v) for e in v.link_edges]
V = sorted(part, key=lambda v: v.index); idx = {v: i for i, v in enumerate(V)}
P = np.array([v.co[:] for v in V])
th = np.arctan2(P[:, 1] - CY, P[:, 0] - CX)
sec = ((th + math.pi) / (2 * math.pi) * NSEC).astype(int) % NSEC
zb = np.zeros(len(P)); r = np.hypot(P[:, 0] - CX, P[:, 1] - CY)
zmin_s = np.array([P[(sec == s) | (sec == (s + 1) % NSEC) | (sec == (s - 1) % NSEC), 2].min() for s in range(NSEC)])
zb_s = zmin_s + BAND
zb = zb_s[sec]
R0_s = np.array([r[(sec == s) & (np.abs(P[:, 2] - zb_s[s]) < 0.005)].mean() if ((sec == s) & (np.abs(P[:, 2] - zb_s[s]) < 0.005)).any() else np.nan for s in range(NSEC)])
R0_s = np.where(np.isnan(R0_s), np.nanmean(R0_s), R0_s)
R0 = R0_s[sec]
nbr = [[idx[e.other_vert(v)] for e in v.link_edges if e.other_vert(v) in idx] for v in V]
fixed = P[:, 2] < zb - 0.01
S = P.copy()
for it in range(SMOOTH):                       # Taubin (lambda/mu): smooths without shrinking the dome
    lam = 0.5 if it % 2 == 0 else -0.53
    L = np.zeros_like(S)
    for i, nb in enumerate(nbr):
        if not fixed[i] and nb:
            L[i] = S[nb].mean(0) - S[i]
    S = S + lam * L
h_s = S[:, 2] - zb; r_s = np.hypot(S[:, 0] - CX, S[:, 1] - CY)
ZTOP = float(np.percentile(P[:, 2], 99)) + RAISE   # a horizontal flat top (the crown's nub left out of the reference)
out = P.copy(); moved = 0
for i in range(len(P)):
    hp = P[i, 2] - zb[i]
    w = min(1.0, max(0.0, hp / 0.012)); w = w * w * (3 - 2 * w)
    if w <= 0:
        continue
    c3 = np.array([CX, CY, zb[i]])
    d = P[i] - c3; s_p = float(np.linalg.norm(d)); dirp = d / max(s_p, 1e-9)
    phi = math.atan2(max(dirp[2], 1e-6), max(math.hypot(dirp[0], dirp[1]), 1e-6))
    s_dome = float(np.linalg.norm(S[i] - c3))
    detail = s_p / max(s_dome, 1e-6)                     # Meshy's folds as a ratio about the smooth dome
    s_side = R0[i] / (math.cos(phi) + TAPER * math.sin(phi))
    s_top = (ZTOP - zb[i]) / math.sin(phi) if math.sin(phi) > 1e-6 else 1e9
    s_t = min(s_side, s_top) * detail
    target = c3 + dirp * s_t
    out[i] = P[i] + w * (target - P[i]); moved += 1
for v, p in zip(V, out):
    v.co = p
bm.normal_update(); bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('CAP_RESHAPE', json.dumps({'verts': len(V), 'moved': moved, 'ztop': round(ZTOP, 3), 'raise': RAISE, 'taper': TAPER,
                                 'zb_range': [round(float(zb_s.min()), 3), round(float(zb_s.max()), 3)],
                                 'max_move_mm': round(float(np.linalg.norm(out - P, axis=1).max()) * 1000, 1)}))
