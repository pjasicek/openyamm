#!/usr/bin/env python3
"""Second opinion on robe_gate.py's flags (PeasantGirl): its signed distance uses the nearest robe face's plane, so in the skirt's deep folds
a shin 4-7 cm inside the cloth reads as 'outside'. For every flagged leg vertex a ray goes horizontally out from the pelvis axis through it
(and 6 more directions fanned +-60 deg); the vertex is really outside only if no ray meets a robe face. Args: <glb> [clips]"""
import sys
src = open(__file__.replace('robe_ray_check.py', 'robe_gate.py')).read().split('res = {}')[0]
sys.argv = [sys.argv[0], sys.argv[1], '/dev/null'] + sys.argv[2:]
exec(src)
def ray_hits(P, o, d):
    T = P[tri[F]]; A, B, C = T[:, 0], T[:, 1], T[:, 2]; e1, e2 = B - A, C - A
    pv = np.cross(d, e2); det = np.einsum('ij,ij->i', e1, pv); ok = np.abs(det) > 1e-12; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
    tv = o - A; u = np.einsum('ij,ij->i', tv, pv) * inv; qv = np.cross(tv, e1); v = (qv @ d) * inv; t = np.einsum('ij,ij->i', e2, qv) * inv
    return (ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)).any()
tot = {}
for clip in [a['name'] for a in m.glb.json['animations']]:
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; n_flag = n_out = 0; worst = 0.0
    for t in np.arange(0, dur + 1e-6, 1 / 24):
        P = allpos(m.world(m.sample(clip, float(t))))
        sd, ff, dist = signed(P, P[legv]); sd = sd * sgn
        bad = np.where((sd > 0.003) & (fh[F[ff]] > 0.14) & (dist < 0.08))[0]
        pel = P[legv].mean(0)
        for i in bad:
            n_flag += 1; q = P[legv[i]]; r = q - pel; r[1] = 0; r /= max(np.linalg.norm(r), 1e-9)
            inside = False
            if clip in ('Death', 'Dead'):           # lying: the cloth must cover the vertex from above (the party looks down on a corpse)
                inside = ray_hits(P, q, np.array([0, 1.0, 0]))
            else:
                for a in np.radians([0, -60, -30, 30, 60]):
                    c, s_ = np.cos(a), np.sin(a); d = np.array([r[0] * c - r[2] * s_, 0, r[0] * s_ + r[2] * c])
                    if ray_hits(P, q, d): inside = True; break
            if not inside: n_out += 1; worst = max(worst, float(sd[i]))
    tot[clip] = (n_flag, n_out, round(worst * 100, 1))
    print(f'{clip:10s} flagged {n_flag:4d}  really outside {n_out:3d}  worst {worst * 100:.1f} cm', flush=True)
