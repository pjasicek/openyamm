"""Right fist round the glaive shaft (after mm9_guard_claude/scripts/finish_guard.py, the grip part; mm6_bar1_claude grip_solve.py).

KROHN.abc keeps the glaive rigid in the right hand in every clip (Xspear's keys only roll it about the shaft, walk, or slide it
0.34 m along the shaft, stand1/fidget3/fidget4/statue: measured), so ONE fist fits every clip:
- the shaft keeps MM9's direction (Xspear -> Xspearmid at rest); its axis is moved into our MPFB fist: through the point G a
  shaft radius plus 12 mm in front of the palm at the finger roots, stepped off the palm skin; Xspear and Xspearmid are
  translated (never turned) onto that axis, so add_props.py places the glaive there and every MM9 key keeps working;
- each finger (index..pinky) is curled on a grid (MCP, PIP, DIP) about the shaft axis to lie R + finger half-thickness + 5 mm
  from it, the curl shared between the joints; the thumb closes over the middle finger on the far side;
- the knuckle line is turned onto the shaft by a constant wrist offset only if they cross by more than WRIST_MIN degrees
  (then the glaive is built turned back so it still points where MM9's does): reported, not applied below.
Writes work/hand_poses.json (bone-local finger rotations 'grip' for grip_keys.py) and the master with the moved joints.
Args: -- <in blend> <out blend> <poses json>"""
import bpy, sys, json, math, os
import numpy as np
from mathutils import Vector, Matrix
IN, OUT, POSES = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R_GRIP = 0.027                                  # make_props.py shaft radius (RS)
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
Wm = np.array(rig.matrix_world)
H = lambda n: (Wm @ np.r_[np.array(rig.data.bones[n].head_local), 1])[:3]
BR = lambda n: Wm[:3, :3] @ np.array(rig.data.bones[n].matrix_local)[:3, :3]
unit = lambda v: v / np.linalg.norm(v)


def rot(ax, a):
    return np.array(Matrix.Rotation(a, 3, Vector(ax)))


U = unit(H('Xspearmid') - H('Xspear'))
GJ = json.load(open(os.path.join(HERE, 'work', 'hands_v1.json')))['joints']['R']
FN = {'Thumb': 1, 'Index': 2, 'Middle': 3, 'Ring': 4, 'Pinky': 5}
J = {f: np.array([GJ[f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ[f'finger{k}-3_tip']]) for f, k in FN.items()}
FINGERS = ('Index', 'Middle', 'Ring', 'Pinky')
kn = unit(J['Index'][0] - J['Pinky'][0])
f0 = unit(np.mean([J[f][1] - J[f][0] for f in FINGERS], 0)); f0 = unit(f0 - kn * (f0 @ kn))
n0 = np.cross(kn, f0)
if (np.mean([J[f][3] for f in FINGERS], 0) - np.mean([J[f][0] for f in FINGERS], 0)) @ n0 < 0:
    n0 = -n0
ang_kn = math.degrees(math.acos(min(1.0, abs(kn @ U))))
# the shaft crosses our knuckle line at ang_kn: as the Guard's, the wrist takes that up (a constant turn of the hand, keyed in
# every clip by grip_keys.py, the glaive's Xspear keys turned back by the same amount so the glaive stays where MM9's is);
# the fist is solved in the unturned hand round the shaft as the turned hand sees it (along the knuckle line)
W_ = H('Bip01 R Hand')
Kn = kn if kn @ U > 0 else -kn
v_ = np.cross(Kn, U); sn_ = np.linalg.norm(v_); th_ = math.atan2(sn_, Kn @ U)
RD = rot(v_ / sn_, th_)                                   # world turn of the hand: knuckle line -> shaft
BH = BR('Bip01 R Hand')
Dloc = Matrix((BH.T @ RD @ BH).tolist()).to_quaternion()
Uw = U.copy()
U = RD.T @ Uw                                             # the shaft in the unturned hand: along the knuckle line
AX = U
print('WRIST turn deg', round(math.degrees(th_), 1))
gid = {g.index: g.name for g in body.vertex_groups}
dom = {}
for v in me.vertices:
    if v.groups:
        g = max(v.groups, key=lambda x: x.weight); dom.setdefault(gid[g.group], []).append(v.index)
COV = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
half = {}
for f in FN:
    ids = sum((dom.get(f'Bip01 R {f}{i}', []) for i in (1, 2, 3)), [])
    Q = COV[ids]; pts = J[f]
    d = np.min([np.linalg.norm(np.cross(Q - a_, unit(b_ - a_)), axis=1) for a_, b_ in zip(pts[:-1], pts[1:])], axis=0)
    half[f] = float(np.percentile(d[d < 0.04], 35))      # reported only (the estimate catches web and palm skin)
HALF = 0.016                                              # MPFB finger radius x 1.86 (measured on the index/middle mid phalanges)
palm = COV[dom.get('Bip01 R Hand', [])]
mcp = np.mean([J[f][0] for f in FINGERS], 0)
G = mcp + f0 * 0.022 + n0 * (R_GRIP + HALF + 0.004)   # power grip: the shaft across the base of the fingers, clear of the finger roots


def _rad(p, c, ax):
    v = p - c; return np.linalg.norm(v - np.outer(v @ ax, ax), axis=-1)


near = np.linalg.norm(palm - mcp, axis=1) < 0.11
step = 0
for step in range(8):                                     # the thenar pad may stay against the shaft (a grip presses into it)
    if _rad(palm[near], G, U).min() >= R_GRIP + 0.004:
        break
    G = G + n0 * 0.001
# fist first (2026-11-04: fitting the fingers to a chosen shaft point laid them over the shaft): curl the middle finger into a
# natural fist (MCP/PIP/DIP shared) whose inner circle (finger skin) holds the shaft radius + 3 mm, and put the shaft axis
# through that circle's centre; the other fingers are then solved round that axis as before
def _fk(j, angs, sign):
    pts = [j[0]]; total = 0.0; p = j[0]
    for i, a in enumerate(angs):
        total += a
        p = p + rot(AX, sign * total) @ (j[i + 1] - j[i])
        pts.append(p)
    return np.array(pts)
_t0 = J['Middle'][3]
_sg = 1.0 if ((rot(AX, 0.3) @ (_t0 - J['Middle'][0])) - (_t0 - J['Middle'][0])) @ n0 > 0 else -1.0
e1 = unit(f0 - AX * (f0 @ AX)); e2 = np.cross(AX, e1)
fbest = None
for a1 in np.radians(np.arange(30, 91, 5)):
    for a2 in np.radians(np.arange(40, 111, 5)):
        for a3 in np.radians(np.arange(15, 76, 5)):
            if a3 > a2:
                continue
            p = _fk(J['Middle'], (a1, a2, a3), _sg)
            q = np.c_[(p - J['Middle'][0]) @ e1, (p - J['Middle'][0]) @ e2]
            A = np.c_[2 * q, np.ones(len(q))]; bb = (q ** 2).sum(1)
            cx, cy, cc = np.linalg.lstsq(A, bb, rcond=None)[0]
            r = math.sqrt(max(cc + cx * cx + cy * cy, 1e-9))
            resid = np.abs(np.linalg.norm(q - [cx, cy], axis=1) - r).max()
            cost = (r - HALF - (R_GRIP + 0.003)) ** 2 + 0.5 * resid ** 2 + 2e-5 * ((a1 - a2) ** 2 + (a2 - 1.5 * a3) ** 2)
            if fbest is None or cost < fbest[0]:
                fbest = (cost, (a1, a2, a3), J['Middle'][0] + cx * e1 + cy * e2, r, resid)
G = fbest[2] + AX * ((mcp - fbest[2]) @ AX)
print('FISTFIT deg', np.round(np.degrees(fbest[1]), 0).tolist(), 'circle r cm', round(fbest[3] * 100, 2), 'resid mm', round(fbest[4] * 1000, 1))
print('GRIP', np.round(G, 3), 'knuckle-shaft deg', round(ang_kn, 1), 'palm steps mm', step,
      'half cm', {k: round(v * 100, 2) for k, v in half.items()})


def radial(p):
    v = p - G; return np.linalg.norm(v - np.outer(v @ U, U), axis=-1)


def fk(j, angs, sign):
    pts = [j[0]]; total = 0.0; p = j[0]
    for i, a in enumerate(angs):
        total += a
        p = p + rot(AX, sign * total) @ (j[i + 1] - j[i])
        pts.append(p)
    return np.array(pts)


def samples(pts):
    s = []
    for a, b in zip(pts[:-1], pts[1:]):
        for t in (0.25, 0.5, 0.75, 1.0):
            s.append(a + (b - a) * t)
    return np.array(s)


tip0 = J['Middle'][3]
sg = 1.0 if ((rot(AX, 0.3) @ (tip0 - J['Middle'][0])) - (tip0 - J['Middle'][0])) @ n0 > 0 else -1.0
out = {}; posed = {}; rep = {'knuckle_shaft_deg': round(ang_kn, 1)}
for f in FINGERS:
    j = J[f]; best = None; want = R_GRIP + HALF + 0.004
    F0 = np.array(fbest[1])
    for d1 in np.radians(np.arange(-24, 25, 4)):
        for d2 in np.radians(np.arange(-24, 25, 4)):
            for d3 in np.radians(np.arange(-20, 21, 5)):
                a1, a2, a3 = F0 + (d1, d2, d3)
                if min(a1, a2, a3) < 0 or a3 > a2 + 1e-6:
                    continue
                p = fk(j, (a1, a2, a3), sg); s_ = samples(p); r = radial(s_)
                # no finger skin inside the shaft (+1 mm), close to it, near the middle finger's natural fist
                c = 400 * (np.minimum(r - (want - 0.002), 0) ** 2).sum() + 0.3 * ((r[2:] - want) ** 2).mean() \
                    + 0.0004 * (d1 * d1 + d2 * d2 + d3 * d3)
                if best is None or c < best[0]:
                    best = (c, (a1, a2, a3), p)
    out[f] = best[1]; posed[f] = best[2]
    rr = radial(samples(best[2]))
    rep[f] = {'deg': np.round(np.degrees(best[1]), 0).tolist(), 'min_clear_mm': round(float((rr - R_GRIP - HALF).min() * 1000), 1)}
    print('FIST', f, rep[f])


def chain_pose(s, f, deltas):
    res = {}; prev = np.eye(3)
    for i, D in enumerate(deltas):
        n = f'Bip01 {s} {f}{i + 1}'; Rb = BR(n)
        B = Rb.T @ prev.T @ D @ Rb
        q = Matrix(B.tolist()).to_quaternion()
        res[n] = [q.x, q.y, q.z, q.w]; prev = D
    return res


grip = {}
for f in FINGERS:
    a1, a2, a3 = out[f]
    grip.update(chain_pose('R', f, [rot(AX, sg * a1), rot(AX, sg * (a1 + a2)), rot(AX, sg * (a1 + a2 + a3))]))
t = J['Thumb']
target = posed['Middle'][2] + unit(posed['Middle'][2] - G) * (half['Middle'] + half['Thumb']) * 0.8
want = R_GRIP + half['Thumb'] + 0.005
best = None
for th in np.radians(np.arange(-60, 101, 5)):
    R1 = rot(f0, th)
    for ph in np.radians(np.arange(-100, 101, 5)):
        R2 = rot(AX, ph) @ R1
        for ps in np.radians(np.arange(0, 76, 6)):
            R3 = rot(AX, ps) @ R2
            p1 = t[0] + R2 @ (t[1] - t[0]); p2 = p1 + R3 @ (t[2] - t[1]); p3 = p2 + R3 @ (t[3] - t[2])
            s_ = samples(np.array([t[0], p1, p2, p3])); r = radial(s_)
            c = np.linalg.norm(p3 - target) + 60 * np.maximum(want - r, 0).sum()
            if best is None or c < best[0]:
                best = (c, (R2, R3), (th, ph, ps), p3, r)
rep['Thumb'] = {'deg': np.round(np.degrees(best[2]), 0).tolist(), 'tip_to_target_mm': round(float(np.linalg.norm(best[3] - target)) * 1000, 1),
                'min_clear_mm': round(float((best[4] - R_GRIP - half['Thumb']).min() * 1000), 1)}
print('THUMB', rep['Thumb'])
grip.update(chain_pose('R', 'Thumb', [best[1][0], best[1][1], best[1][1]]))
rep['wrist_turn_deg'] = round(math.degrees(th_), 1)
json.dump(dict(grip=grip, relaxed={}, report=rep, hand_offset={'Bip01 R Hand': [Dloc.x, Dloc.y, Dloc.z, Dloc.w]},
               child_inverse={'Xspear': [-Dloc.x, -Dloc.y, -Dloc.z, Dloc.w]}), open(POSES, 'w'), indent=0)
# move Xspear / Xspearmid onto the world shaft through the turned fist centre (translation only)
Gw = W_ + RD @ (G - W_)
xs0, xm0 = H('Xspear'), H('Xspearmid')
to_axis = lambda p: Gw + Uw * ((p - Gw) @ Uw)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
Mi = np.linalg.inv(Wm)
d = Mi[:3, :3] @ (to_axis(xs0) - xs0)                 # both on one line: the same move keeps the shaft rigid
for n in ('Xspear', 'Xspearmid'):
    eb = rig.data.edit_bones[n]
    eb.head += Vector(d); eb.tail += Vector(d)
bpy.ops.object.mode_set(mode='OBJECT')
print('SPEAR moved m', np.round(to_axis(xs0) - xs0, 4).tolist())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
