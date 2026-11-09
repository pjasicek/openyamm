#!/usr/bin/env python3
"""Right fist on the staff, solved on the hand's skin (2026-11-01; replaces the joint-point solve of r1-r13).

r1-r13 put the staff where the finger JOINTS (bone centre lines) sat 2.3-3.3 cm from its axis, with no test on the palm. Our hand is a Meshy
claw (fingers bent about 90 deg at the knuckles in the bind), so the solve opened the knuckles 18-28 deg, left the middle joints straight and
the staff stood 4.8 cm off the knuckles on the palm side: palm skin 2.1 cm off the shaft, the fingertips beside it (user review 2026-11-01).

Here, in the bind (glTF frame, the GLB's own inverse binds; vertices rigid with their leading bone):
- seat: the staff axis is moved (translation only, its direction is kept) to sit under the palm: for each position along the finger
  direction, lifted until the palm skin (R Hand vertices and the finger and thumb skin within 20 % of the knuckle) is CL off the shaft
  surface; the position whose solved fist scores best is kept (2.15 cm from the r13 point);
- fingers: per joint, from knuckle to tip, the curl about the staff axis direction is the largest angle reached from the extended side
  before the joint's own phalanx (beyond the 20 % next to the joint, which hardly moves) or the phalanges beyond it (minus the 30 % next to
  their base joint, which cannot reach the shaft before this phalanx does) come within CL of the shaft surface; a joint never swings
  through the shaft. Knuckles may open (down to -50 deg) where the claw already crosses the shaft, middle and last joints 25 deg;
  no finger joint curls over 85 deg (r7's cap against folded faces);
- thumb: the same rule with the opposite sense, with the solved index and middle fingers' skin as a further obstacle (3 mm); then the
  thumb is turned 30 deg about the finger direction and given the same curls at its turned joints, so it crosses the shaft's front with
  its pads on the wood instead of curling into the front coat sector (checked on the skin by grip_gate.py and arm_hand_gate.py).
Use: grip_solve.py seat <glb> (writes rig.json grip.point and moves the staff and staff skull in work/asm4.npz, uv_v1.npz, uv_tex.npz; backups
work/*_pre_seat.npz once); grip_keys.py imports solve()."""
import sys, json
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
RS = 0.0165; CL = 0.0025; THUMB_CL = 0.003      # 2.5 mm: a 1 mm palm clearance put the pinky 1 mm into the shaft
FINGERS = ('Index', 'Middle', 'Ring', 'Pinky')
THUMB_TWIST = -30.0                                                    # deg about the finger direction, before the curl
def g(p): return np.array([p[0], p[2], -p[1]], float)
def gi(p): return np.array([p[0], -p[2], p[1]], float)
def rot(axis, th):
    axis = axis / np.linalg.norm(axis); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K

def hand_data(m):
    """Bind world matrices of the R hand bones and the body vertices led by each (bind positions)."""
    nn = [n['name'] for n in m.glb.json['nodes']]; jn = [nn[j] for j in m.joints]
    Wb = {jn[k]: np.linalg.inv(m.inverse_binds[k]) for k in range(len(jn))}
    pb = m.primitives[0]; V = pb['positions']; dom = np.array([jn[j] for j in pb['joints'][np.arange(len(V)), np.argmax(pb['weights'], 1)]])
    bones = ['Bip01 R Hand'] + [f'Bip01 R {f}{k}' for f in FINGERS + ('Thumb',) for k in (1, 2, 3)]
    verts = {b: V[dom == b] for b in bones}
    return Wb, verts

class Axis:
    def __init__(self, G, A): self.G = G; self.A = A / np.linalg.norm(A)
    def gap(self, P):
        d = P - self.G; return np.linalg.norm(d - np.outer(d @ self.A, self.A), axis=1) - RS

def solve(Wb, verts, G, A, n_palm, tips):
    """Returns ({bone: posed world matrix}, report). tips: {finger: bind tip position} (glTF frame)."""
    ax = Axis(G, A); A = ax.A
    W = {b: Wb[b].copy() for b in Wb}; P = {b: v.copy() for b, v in verts.items()}; TP = {f: tips[f].copy() for f in tips}
    rep = {}
    fd = np.mean([Wb[f'Bip01 R {f}1'][:3, 3] for f in FINGERS], 0) - Wb['Bip01 R Hand'][:3, 3]
    h_f = A if np.cross(A, fd) @ n_palm > 0 else -A                  # curl towards the palm side
    def chain(f): return [f'Bip01 R {f}{k}' for k in (1, 2, 3)]
    def pad(b, Q, nxt):
        h = W[b][:3, 3]; d = nxt - h; L = np.linalg.norm(d); d /= L; s = (Q - h) @ d
        return Q[s >= np.median(s)] if len(Q) else Q, h, d, L
    def solve_chain(f, h, lo, hi, obstacles=None, cl=CL):
        bs = chain(f); angs = []
        for k in range(3):
            piv = W[bs[k]][:3, 3].copy()
            def nxt_of(j): return W[bs[j + 1]][:3, 3] if j < 2 else TP[f]
            # vertices tested: this phalanx's distal half, the later phalanges beyond 30 % of their length from their base joint
            tests = []
            for j in range(k, 3):
                Q = P[bs[j]]
                if not len(Q): continue
                hj = W[bs[j]][:3, 3]; d = nxt_of(j) - hj; L = np.linalg.norm(d); d /= L; s = (Q - hj) @ d
                tests.append(Q[s >= (0.2 if j == k else 0.3) * L])
            T = np.vstack(tests) if tests else np.zeros((0, 3))
            ths = np.radians(np.arange(lo[k], hi + 0.01, 0.5)); gaps = []
            for th in ths:
                Rk = rot(h, th); Tq = piv + (T - piv) @ Rk.T; gp = ax.gap(Tq).min()
                if obstacles is not None and len(obstacles):
                    dd = np.linalg.norm(Tq[:, None] - obstacles[None], axis=2).min(); gp = min(gp, dd - (THUMB_CL - cl))
                gaps.append(gp)
            gaps = np.array(gaps); free = gaps > cl
            if free.all(): th = ths[int(np.argmin(gaps))]                       # never reaches the shaft: closest approach
            elif not free[0]:                                                  # in contact from the extended end: the least deep angle
                stop = int(np.argmin(gaps)) + 1                                # on the near side of the deepest angle (never swing through)
                th = ths[int(np.argmax(gaps[:stop]))]
            else:
                i0 = int(np.argmax(free)); i1 = i0
                while i1 + 1 < len(free) and free[i1 + 1]: i1 += 1
                th = ths[i1]
            Rk = rot(h, th)
            for j in range(k, 3):
                b = bs[j]; W[b][:3, :3] = Rk @ W[b][:3, :3]; W[b][:3, 3] = piv + Rk @ (W[b][:3, 3] - piv); P[b] = piv + (P[b] - piv) @ Rk.T
            TP[f] = piv + Rk @ (TP[f] - piv); angs.append(round(float(np.degrees(th)), 1))
        return angs
    for f in FINGERS:
        rep[f] = dict(curl_deg=solve_chain(f, h_f, (-50, -25, -25), 85))          # 85: r7's cap (a 100 deg index tip folded a face)
    obst = np.vstack([P[f'Bip01 R {f}{k}'] for f in ('Index', 'Middle') for k in (1, 2, 3)])
    # thumb: ours lies along the shaft (its first bone about 36 deg off the axis); turning it across first (0-60 deg) was tried: 15 deg further
    # round the shaft, but its short last phalanx then lifts 3 mm further off, so it is not done. Instead it is first turned THUMB_TWIST about
    # the finger direction: the shaft's far side lies against the front coat sector, and the curled thumb went 3.1 cm into it (r18, Aware;
    # r13 2.2 cm). Turned, it crosses the shaft's front with its pads on the wood and clears the coat
    tb = chain('Thumb'); snap = ({b: W[b].copy() for b in tb}, {b: P[b].copy() for b in tb}, TP['Thumb'].copy())
    angs = solve_chain('Thumb', -h_f, (-45, -25, -25), 90, obstacles=obst, cl=CL)       # the curl, solved untwisted
    for b in tb: W[b] = snap[0][b].copy(); P[b] = snap[1][b].copy()
    TP['Thumb'] = snap[2].copy()
    e1 = fd - (fd @ A) * A; e1 /= np.linalg.norm(e1)
    def turn(b0, piv, R_):
        for b in tb[b0:]: W[b][:3, :3] = R_ @ W[b][:3, :3]; W[b][:3, 3] = piv + R_ @ (W[b][:3, 3] - piv); P[b] = piv + (P[b] - piv) @ R_.T
        TP['Thumb'] = piv + R_ @ (TP['Thumb'] - piv)
    turn(0, W[tb[0]][:3, 3].copy(), rot(e1, np.radians(THUMB_TWIST)))                  # twist, then the same curls at the turned joints
    for k in range(3): turn(k, W[tb[k]][:3, 3].copy(), rot(-h_f, np.radians(angs[k])))
    rep['Thumb'] = dict(curl_deg=angs, twist_deg=THUMB_TWIST)
    # report: per phalanx the distal-half gap to the shaft surface (cm), palm gap, thumb angle round the axis from the palm
    for f in FINGERS + ('Thumb',):
        gs = []
        for k, b in enumerate(chain(f)):
            Q = P[b]
            if not len(Q): gs.append(None); continue
            nxt = W[chain(f)[k + 1]][:3, 3] if k < 2 else TP[f]
            q, *_ = pad(b, Q, nxt); gs.append(round(float(ax.gap(q).min()) * 100, 2))
        rep[f]['pad_gap_cm'] = gs
    pv = P['Bip01 R Hand']; rep['palm_gap_cm'] = round(float(ax.gap(pv).min()) * 100, 2)
    allv = np.vstack([P[b] for b in P]); rep['inside_cm'] = round(float(max(0.0, -ax.gap(allv).min())) * 100, 2)
    return W, rep, P

def score(rep):
    s = 0.0
    for f in FINGERS:
        pg = [x for x in rep[f]['pad_gap_cm'] if x is not None]
        s += sum(max(0.0, x - 0.3) for x in pg[1:]) + 0.5 * max(0.0, pg[0] - 0.3) + 0.02 * max(0.0, -rep[f]['curl_deg'][0] - 10)
    tg = [x for x in rep['Thumb']['pad_gap_cm'] if x is not None]
    s += 0.5 * max(0.0, tg[-1] - 0.3) + 10 * rep['inside_cm'] + 2 * abs(rep["palm_gap_cm"] - CL * 100)
    return s

if __name__ == '__main__' and sys.argv[1] == 'seat':
    m = Model(Glb(sys.argv[2])); Wb, verts = hand_data(m)
    R = json.load(open('work/rig.json')); GR = R['grip']; F = R['fingers']
    G0 = g(GR['point']); A = g(GR['axis']); A /= np.linalg.norm(A); n_palm = g(GR['palm_side']); n_palm /= np.linalg.norm(n_palm)
    tips = {f: g(F[f][3]) for f in FINGERS + ('Thumb',)}
    fd = g(GR['finger_dir']); e1 = fd - (fd @ A) * A; e1 /= np.linalg.norm(e1); e2 = np.cross(A, e1)
    if e2 @ n_palm > 0: e2 = -e2                                         # e2: from the axis towards the back of the hand
    # the palm: R Hand skin plus the skin next to the knuckles and the thumb root (within 20 % of the bone, which no curl moves away)
    palm = [verts['Bip01 R Hand']]
    for f in FINGERS + ('Thumb',):
        b = f'Bip01 R {f}1'; h = Wb[b][:3, 3]; d = Wb[f'Bip01 R {f}2'][:3, 3] - h; L = np.linalg.norm(d)
        palm.append(verts[b][(verts[b] - h) @ d / L < 0.2 * L])
    palm = np.vstack(palm)
    best = None
    for de1 in np.arange(-0.05, 0.0051, 0.00125):
        # lift along e2 (towards the palm) until the palm skin is CL off the surface
        lo_, hi_ = -0.04, 0.06
        for _ in range(40):
            mid = 0.5 * (lo_ + hi_); Gc = G0 + e1 * de1 + e2 * mid
            if Axis(Gc, A).gap(palm).min() > CL: lo_ = mid
            else: hi_ = mid
        Gc = G0 + e1 * de1 + e2 * lo_
        _, rep, _ = solve(Wb, verts, Gc, A, n_palm, tips); sc = score(rep)
        print(f'seat e1 {de1*100:5.1f} e2 {lo_*100:5.2f} cm  score {sc:6.2f}  palm {rep["palm_gap_cm"]}  inside {rep["inside_cm"]}  '
              + '  '.join(f'{f[:2]} {rep[f]["curl_deg"]} {rep[f]["pad_gap_cm"]}' for f in FINGERS + ('Thumb',)))
        if best is None or sc < best[0]: best = (sc, de1, lo_, Gc, rep)
    sc, de1, de2, Gn, rep = best
    print('SEAT best e1', round(de1 * 100, 2), 'e2', round(de2 * 100, 2), 'cm, offset', round(float(np.linalg.norm(Gn - G0)) * 100, 2), 'cm')
    if '--write' in sys.argv:
        import os, shutil
        delta_bl = gi(Gn - G0)
        for f in ('work/asm4.npz', 'work/uv_v1.npz', 'work/uv_tex.npz'):
            bk = f.replace('.npz', '_pre_seat.npz')
            if not os.path.exists(bk): shutil.copy2(f, bk)
            D = dict(np.load(f, allow_pickle=True)); names = [str(x) for x in D['names']]
            sel = np.isin(D['comp'], [names.index('staff'), names.index('sskull')])
            D['co'] = D['co'].copy(); D['co'][sel] += delta_bl
            tmp = f.replace('.npz', '_tmp.npz'); np.savez(tmp, **D); os.replace(tmp, f); print('moved', int(sel.sum()), 'staff vertices in', f)
        GR.setdefault('point_r13', GR['point']); GR['point'] = (np.array(GR['point']) + delta_bl).tolist()
        tot = np.array(GR['point']) - np.array(GR['point_r13'])            # cumulative from the r13 grip point (Blender frame)
        GR['seat'] = dict(last_e1_cm=round(de1 * 100, 2), last_e2_cm=round(de2 * 100, 2), offset_from_r13_blender=tot.tolist(),
                          offset_from_r13_cm=round(float(np.linalg.norm(tot)) * 100, 2))
        tmp = 'work/rig_tmp.json'; json.dump(R, open(tmp, 'w'), indent=0); os.replace(tmp, 'work/rig.json'); print('rig.json grip.point updated')
