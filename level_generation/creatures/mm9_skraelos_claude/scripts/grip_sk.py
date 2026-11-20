#!/usr/bin/env python3
"""Held props and the grip, baked into the bind (positions only; UVs untouched, so it may run after the paint).
- STAFF (right hand): MM9's staff relative to MM9's R Hand at its Standing first pose (R Finger1 is turned ~15 deg in every MM9 clip, so
  the staff rides on the Hand with that turn baked in), carried onto our R Hand; then moved (translation only) so its axis runs on the palm
  side of our proximal phalanges, STAFF_GAP off their centres.
- HELD SKULL (left hand): the skull mesh, SKULL_W wide, upright and facing forward when the left arm hangs in Standing, its centre on the
  palm side of the left proximal phalanges; added after the UVs as a copy of the head (work/held_skull.json holds the transform).
- GRIP: per digit and joint (base to tip), the joint turns the rest of the digit toward the prop by the least angle that brings it into
  contact (signed distance <= CONTACT), capped at MAXDEG; the pieces are rigid per bone. The fingers keep this grip in every clip.
Args: <asm npz with staff> <rig json> <mm9 glb> <our clips glb> <skull npz> <out npz>"""
import sys, json, os
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
A_, R_, MG, CG, SK, OUT = sys.argv[1:7]
E = lambda k, d: float(os.environ.get(k, d))
D = dict(np.load(A_)); co = D['co'].copy(); comp = D['comp']; names = [str(x) for x in D['names']]; hp = D['hand_piece']
R = json.load(open(R_)); GR = {int(k): v for k, v in R['groups'].items()}; chains = json.loads(str(D['chains']))
def g(p): p = np.atleast_2d(p); return np.c_[p[:, 0], p[:, 2], -p[:, 1]]
def b(p): p = np.atleast_2d(p); return np.c_[p[:, 0], -p[:, 2], p[:, 1]]
def gm(M):   # a glTF-space rigid matrix as a Blender-space one
    C = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]]); return C @ M @ np.linalg.inv(C)
mm = Model(Glb(MG)); mn = [n.get('name') for n in mm.glb.json['nodes']]
Wr = mm.world({}); Ws = mm.world(mm.sample('stand', 0.0))
cm = Model(Glb(CG)); cn = [n.get('name') for n in cm.glb.json['nodes']]
Cr = cm.world({}); Cs = cm.world(cm.sample('Standing', 0.0))
def W(model_w, nn, n): return gm(model_w[nn.index(n)])
def rot(axis, th):
    axis = axis / np.linalg.norm(axis); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K
def piece_mask(side, k):
    return hp == (k if side == 'R' else -k - 1)
def palm_side(side):
    """Unit vector from the proximal phalanges toward where the fingers curl (the palm side), and the proximal centre."""
    v = []; cs = []
    for f in ('Index', 'Middle', 'Ring', 'Pinky'):
        J = [np.array(p) * ([1, 1, 1] if side == 'R' else [-1, 1, 1]) for p in R['fingers'][f]]
        d = J[1] - J[0]; d /= np.linalg.norm(d); c = J[3] - J[0]; c -= d * (c @ d); v.append(c / np.linalg.norm(c)); cs.append(0.5 * (J[0] + J[1]))
    n = np.mean(v, 0); return n / np.linalg.norm(n), np.mean(cs, 0), np.mean([np.array(R['fingers'][f][1]) - np.array(R['fingers'][f][0]) for f in ('Index', 'Middle', 'Ring')], 0)
# ---------------- staff
si = names.index('staff'); sv = np.where(comp == si)[0]
T_r = W(Cr, cn, 'FHP R Hand') @ np.linalg.inv(W(Ws, mn, 'FHP R Hand')) @ W(Ws, mn, 'FHP R Finger1') @ np.linalg.inv(W(Wr, mn, 'FHP R Finger1'))
T_now = W(Cr, cn, 'FHP R Finger1') @ np.linalg.inv(W(Wr, mn, 'FHP R Finger1'))   # how staff_place.py put it
P0 = co[sv]; Pm = (np.linalg.inv(T_now) @ np.c_[P0, np.ones(len(P0))].T).T      # back to MM9's rest
Ps = (T_r @ Pm.T).T[:, :3]
cst = Ps.mean(0); ust = np.linalg.svd(Ps - cst)[2][0]
npR, pcR, fdR = palm_side('R')
nperp = npR - ust * (npR @ ust); nperp /= np.linalg.norm(nperp)
on_axis = cst + ust * ((pcR - cst) @ ust)
fdn = fdR / np.linalg.norm(fdR); fdn = fdn - ust * (fdn @ ust); fdn /= np.linalg.norm(fdn)
shift = (pcR + nperp * E('STAFF_GAP', '0.024') + fdn * E('STAFF_DIST', '0')) - on_axis
shift -= ust * (shift @ ust)
Ps += shift
# STAFF_OUT: turn the staff about the grip point so that, in Standing, its lower end swings away from the body (outward, +x for the right
# hand in the raw ABC frame) by that many degrees (the fuller robe than MM9's: the staff's foot ran through the hem)
SO = E('STAFF_OUT', '0')
if SO:
    HsR, HrR = W(Cs, cn, 'FHP R Hand'), W(Cr, cn, 'FHP R Hand'); Mrs = HsR @ np.linalg.inv(HrR)
    gp = pcR + nperp * E('STAFF_GAP', '0.024') + fdn * E('STAFF_DIST', '0')
    ps = (Mrs @ np.c_[Ps, np.ones(len(Ps))].T).T[:, :3]; gs = (Mrs @ np.r_[gp, 1])[:3]
    us = Mrs[:3, :3] @ ust; low = -us if us[2] > 0 else us          # the staff's lower direction in Standing
    axis_ = np.cross(low, [1.0, 0, 0]); axis_ /= np.linalg.norm(axis_)
    Rr = max((rot(axis_, np.radians(SO)), rot(axis_, -np.radians(SO))), key=lambda R_: (R_ @ low)[0])
    ps = (ps - gs) @ Rr.T + gs
    Ps = (np.linalg.inv(Mrs) @ np.c_[ps, np.ones(len(ps))].T).T[:, :3]; ust = np.linalg.svd(Ps - Ps.mean(0))[2][0]
    print('STAFF out', SO, 'deg in Standing')
co[sv] = Ps; cst = Ps.mean(0)
print('STAFF axis', ust.round(3), 'moved', round(float(np.linalg.norm(shift)), 3), 'palm side', npR.round(3))
tt = (Ps - cst) @ ust; rad = np.linalg.norm(Ps - cst - np.outer(tt, ust), axis=1)
order = np.argsort(tt); tts, rads = tt[order], rad[order]
def staff_sd(p):
    t = (p - cst) @ ust; perp = np.linalg.norm(p - cst - np.outer(t, ust), axis=1)
    r = np.interp(t, tts, rads); return perp - r
# ---------------- held skull (left)
S = np.load(SK); sco = S['co']; slab = S['label']; keep = slab != 3
k = E('SKULL_W', '0.125') / float(S['width'])
sloc = (sco - S['eye_c']) * k; sloc -= 0.5 * (sloc[keep].min(0) + sloc[keep].max(0))     # centred on its box
# upright and facing forward (-y) in Standing: the rest rotation is the left hand's stand -> rest turn
Hs, Hr = W(Cs, cn, 'FHP L Hand'), W(Cr, cn, 'FHP L Hand')
Rk = (Hr @ np.linalg.inv(Hs))[:3, :3]
npL, pcL, fdL = palm_side('L')
half = float(np.ptp(sloc[keep] @ (Rk.T @ npL)) * 0.5) if False else 0.5 * E('SKULL_W', '0.125') * 1.15
cskull = pcL + npL * (half + E('SKULL_GAP', '0.010')) + fdL / np.linalg.norm(fdL) * E('SKULL_ALONG', '0.02')
if os.environ.get('SKULL_MODE') == 'tips':   # the crown in the curled fingers: beyond the mean fingertip, along knuckles -> tips
    tipsL = np.mean([np.array(R['fingers'][f][3]) * [-1, 1, 1] for f in ('Index', 'Middle', 'Ring', 'Pinky')], 0)
    kn = np.mean([np.array(R['fingers'][f][0]) * [-1, 1, 1] for f in ('Index', 'Middle', 'Ring', 'Pinky')], 0)
    td = (tipsL - kn) / np.linalg.norm(tipsL - kn)
    cskull = tipsL + td * E('SKULL_ALONG', '0.03') + npL * E('SKULL_GAP', '0.0')
if os.environ.get('SKULL_MODE') == 'hold':   # seated against the knuckles and proximal phalanges on the palm side, fingers to curl round it
    tipsL = np.mean([np.array(R['fingers'][f][3]) * [-1, 1, 1] for f in ('Index', 'Middle', 'Ring', 'Pinky')], 0)
    kn = np.mean([np.array(R['fingers'][f][0]) * [-1, 1, 1] for f in ('Index', 'Middle', 'Ring', 'Pinky')], 0)
    td = (tipsL - kn) / np.linalg.norm(tipsL - kn); pn = npL - td * (npL @ td); pn /= np.linalg.norm(pn)
    cskull = kn + td * E('SKULL_ALONG', '0.05') + pn * E('SKULL_GAP', '0.05')
sk_rest = sloc @ Rk.T + cskull
skd = cKDTree(sk_rest[keep]); stri = S['tri']
fn = np.cross(sk_rest[stri[:, 1]] - sk_rest[stri[:, 0]], sk_rest[stri[:, 2]] - sk_rest[stri[:, 0]]); vn = np.zeros_like(sk_rest)
for c_ in range(3): np.add.at(vn, stri[:, c_], fn)
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12); kidx = np.where(keep)[0]
cr_ = sk_rest[slab == 0]; SC = 0.5 * (cr_.min(0) + cr_.max(0)); SR = E('SKULL_R', '0.062')
from scipy.spatial import Delaunay
_hull = Delaunay(sk_rest[keep]); _kdk = cKDTree(sk_rest[keep])
def skull_sd(p):   # distance to the skull's vertices, negative inside its convex hull (the skull is near convex)
    p = np.atleast_2d(p); d, _ = _kdk.query(p); return np.where(_hull.find_simplex(p) >= 0, -d, d)
json.dump(dict(scale=k, R=Rk.tolist(), centre=cskull.tolist(), eye_c=np.asarray(S['eye_c']).tolist(), box_mid=(0.5 * (((sco - S['eye_c']) * k)[keep].min(0) + ((sco - S['eye_c']) * k)[keep].max(0))).tolist()),
          open(HERE / 'work/held_skull.json', 'w'), indent=0)
print('SKULL centre', cskull.round(3), 'palm side', npL.round(3))
# ---------------- grip solve
CONTACT = E('CONTACT', '0.002'); MAXDEG = E('MAXDEG', '100')
def skull_sd_n(p):   # signed by the nearest skull vertex's normal (concave face parts read right, unlike the hull)
    p = np.atleast_2d(p); d, i = skd.query(p); q = kidx[i]; s_ = np.sign(np.sum((p - sk_rest[q]) * vn[q], 1)); return d * np.where(s_ == 0, 1, s_)
def hold_fingers():
    """Left hand round the skull (SKULL_MODE hold): per digit and joint (base to tip) the flexion angle (fingers: about the axis across the
    finger toward the palm side; thumb: toward the skull's centre) whose remaining digit comes closest to the skull without entering it."""
    mir = np.array([-1, 1, 1])
    for f, ch in chains.items():
        J = [np.array(p) * mir for p in R['fingers'][f]]
        masks = {s_: np.zeros(len(co), bool) for s_ in (1, 2, 3)}
        for kk, gname in GR.items():
            if gname.startswith(f): masks[int(gname[-1])] |= piece_mask('L', kk)
        tot = []
        for j in (1, 2, 3):
            mv = masks[j].copy()
            for jj in range(j + 1, 4): mv |= masks[jj]
            if not mv.any(): tot.append(0); continue
            pts = co[mv]; Jj = J[j - 1]; dseg = J[j] - Jj
            towards = (SC - 0.5 * (J[j] + Jj)) if f == 'Thumb' else npL
            ax_ = np.cross(dseg, towards); ax_ /= np.linalg.norm(ax_)
            best = None
            for deg in np.arange(E('OPEN_MIN', '-50'), E('MAXDEG', '110') + 0.5, 1.0):
                q = (pts - Jj) @ rot(ax_, np.radians(deg)).T + Jj; m_ = skull_sd_n(q).min()
                if m_ < -0.0015: continue
                if best is None or m_ < best[1] or (abs(m_ - best[1]) < 1e-4 and abs(deg) < abs(best[0])): best = (deg, m_)
            deg = best[0] if best is not None else 0.0
            if best is not None and best[1] > E('REACH', '0.03'): deg = min(deg, E('FREE_DEG', '35'))   # out of reach: a natural curl
            Rm = rot(ax_, np.radians(deg)); co[mv] = (co[mv] - Jj) @ Rm.T + Jj
            for jj in range(j, 4): J[jj] = (J[jj] - Jj) @ Rm.T + Jj
            tot.append(round(float(deg), 1))
        m_all = skull_sd_n(co[masks[1] | masks[2] | masks[3]]).min()
        print('HOLD L', f, 'deg', tot, 'min signed distance to the skull', round(float(m_all), 4))
for side, sd in (('R', staff_sd), ('L', skull_sd)):
    if side == 'L' and os.environ.get('SKULL_MODE') == 'hold':
        hold_fingers(); continue
    mir = np.array([1, 1, 1]) if side == 'R' else np.array([-1, 1, 1])
    for f, ch in chains.items():
        J = [np.array(p) * mir for p in R['fingers'][f]]
        segs = {1: [], 2: [], 3: []}
        for kk, gname in GR.items():
            if gname.startswith(f):
                segs[int(gname[-1])].append(kk)
        masks = {s: np.zeros(len(co), bool) for s in (1, 2, 3)}
        for s_, ks in segs.items():
            for kk in ks: masks[s_] |= piece_mask(side, kk)
        pre = sd(co[masks[1] | masks[2] | masks[3]]).min()
        tot = []
        for j in (1, 2, 3):
            mv = masks[j] | (masks[2] if j < 2 else False) | (masks[3] if j < 3 else False)
            if not mv.any(): tot.append(0); continue
            pts = co[mv]; Jj = J[j - 1]; dseg = J[j] - Jj; mid = 0.5 * (J[j] + Jj)
            # toward the prop: the gradient of the signed distance at the segment's middle
            e = 1e-3; gr = np.array([(sd(mid[None] + e * np.eye(3)[i])[0] - sd(mid[None] - e * np.eye(3)[i])[0]) / (2 * e) for i in range(3)])
            ax_ = np.cross(dseg, -gr)
            if np.linalg.norm(ax_) < 1e-9: tot.append(0); continue
            best = None
            if sd(pts).min() < CONTACT:   # already into the prop: open the joint the least that clears it
                for deg in np.arange(0, -60.5, -0.5):
                    Rm = rot(ax_, np.radians(deg)); q = (pts - Jj) @ Rm.T + Jj
                    if sd(q).min() >= CONTACT: best = deg; break
                if best is None: best = -60.0
            for deg in (np.arange(0, MAXDEG + 0.5, 0.5) if best is None else []):
                Rm = rot(ax_, np.radians(deg)); q = (pts - Jj) @ Rm.T + Jj
                if sd(q).min() <= CONTACT:
                    best = deg; break
            if best is None: best = E('FREE_DEG', '35')
            best = best - E('BACKOFF', '0') if best > 0 else best
            Rm = rot(ax_, np.radians(best)); co[mv] = (co[mv] - Jj) @ Rm.T + Jj
            for jj in range(j, 4): J[jj] = (J[jj] - Jj) @ Rm.T + Jj
            tot.append(best)
        post = sd(co[masks[1] | masks[2] | masks[3]]).min()
        print('GRIP', side, f, 'deg', tot, 'min signed distance before', round(float(pre), 4), 'after', round(float(post), 4))
D['co'] = co
np.savez(OUT, **D)
print('SAVED', OUT)
