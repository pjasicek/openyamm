"""MM6 guard copy of mm9_guard_claude/scripts/finish_guard.py: grip solve, Xbase/Xmid onto the fist axis, half-joint helpers,
hem and nape weights; no linings, no elbow fins, no shoulder fans (MM9 mesh faults); the halberd stays the MM6 attachment (our own
model from mm6_gua_claude), placed by work/halberd_place.json (grip at G, shaft along U, axe toward -W as MM9's big blade).
After the paint (UVs frozen), on the rigged master; nothing here touches the painted faces or their UVs.
- lining: open rims (gauntlet cuffs, boot tops, helmet, collar and shoulder cap, elbow fins) are single-sided, so a view past a rim showed the background (Yrsa's
  sleeves). Three face rings from each rim get a coincident inner copy, flipped, same weights, on one dark texel of the set (work/dark_texel.json).
- halberd (work/halberd.npz, scripts/make_halberd.py): MM9's pole direction and blade plane, moved so that its axis runs through the fist; rigid on Xbase (MM9's Xbase and Xmid
  never move against each other or the hand), faces attribute `pole`.
- fist: fingers solved round the shaft per finger on a grid, the thumb over them (finish_skelwar.py); bone-local rotations in work/hand_poses.json, keyed by finger_keys.py.
Args: <in blend> <out blend> <hand poses json>"""
import bpy, bmesh, sys, json, math, os
import numpy as np
from mathutils import Vector, Matrix
IN, OUT, POSES = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
Wm = np.array(rig.matrix_world)
H = lambda n: (Wm @ np.r_[np.array(rig.data.bones[n].head_local), 1])[:3]
T = lambda n: (Wm @ np.r_[np.array(rig.data.bones[n].tail_local), 1])[:3]
BR = lambda n: Wm[:3, :3] @ np.array(rig.data.bones[n].matrix_local)[:3, :3]
unit = lambda v: v / np.linalg.norm(v)
FINGERS = ('Index', 'Middle', 'Ring', 'Pinky')
ch = lambda s, f: np.array([H(f'Bip01 {s} {f}{i}') for i in (1, 2, 3)] + [T(f'Bip01 {s} {f}3')])


def rot(ax, a):
    return np.array(Matrix.Rotation(a, 3, Vector(ax)))


# --- grip (mm6_bar1_claude/scripts/grip_solve.py): the shaft keeps MM9's direction, tilted 4 deg so the butt clears the right boot; its axis moves into our fist, off the palm skin.
# Chains come from the graft's own joints (the bones' tails point along MM9's mitten frames, not along the fingers: the first solve curled fingers through the shaft)
U0 = unit(H('Xbase') - H('Xmid'))                               # spike -> butt
out_d = np.array([-0.578, -0.471, 0.666]); out_d = unit(out_d - U0 * (out_d @ U0))
U = unit(U0 + out_d * 0.07)
GJ = json.load(open(os.path.join(HERE, 'work', 'hands_v1r.json')))['joints']['R']   # rolled right hand (rotate_hand.py)
FN = {'Thumb': 1, 'Index': 2, 'Middle': 3, 'Ring': 4, 'Pinky': 5}
J = {f: np.array([GJ[f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ[f'finger{k}-3_tip']]) for f, k in FN.items()}
FINGERS = ('Index', 'Middle', 'Ring', 'Pinky')
kn = unit(J['Index'][0] - J['Pinky'][0])
f0 = unit(np.mean([J[f][1] - J[f][0] for f in FINGERS], 0)); f0 = unit(f0 - kn * (f0 @ kn))
n0 = np.cross(kn, f0)
if (np.mean([J[f][3] for f in FINGERS], 0) - np.mean([J[f][0] for f in FINGERS], 0)) @ n0 < 0:
    n0 = -n0
# MM9's pole crosses our knuckle line at 26 deg, so index and pinky cannot both reach it (the hand looked set beside the shaft). As a real hand does, the wrist takes that up: a constant ulnar turn of the hand
# about the palm normal, keyed in every clip (finger_keys.py), and the pole is built turned back by the same angle in the hand's frame, so it still points where MM9's points.
W_ = H('Bip01 R Hand')
Kn = kn if kn @ U > 0 else -kn
v_ = np.cross(Kn, U); sn_ = np.linalg.norm(v_); th_ = math.atan2(sn_, Kn @ U)   # the least turn from the knuckle line to the pole
RD = rot(v_ / sn_, th_)
BH = BR('Bip01 R Hand')
Dloc = Matrix((BH.T @ RD @ BH).tolist()).to_quaternion()
Uw = U.copy(); U = RD.T @ U                                      # the axis in the unturned hand: along the knuckle line
print('WRIST turn deg', round(math.degrees(th_), 1), 'axis-knuckle deg now', round(math.degrees(math.acos(min(1, abs(kn @ U)))), 1))
R_GRIP = 0.0165
# finger half-thickness and the palm skin, from the mesh
gid = {g.index: g.name for g in body.vertex_groups}
dom = {}
for v in me.vertices:
    if v.groups:
        g = max(v.groups, key=lambda x: x.weight); dom.setdefault(gid[g.group], []).append(v.index)
half = {}
COV = np.array([tuple(v.co) for v in me.vertices])
for f in FN:
    ids = sum((dom.get(f'Bip01 R {f}{i}', []) for i in (1, 2, 3)), [])
    Q = COV[ids]; pts = J[f]
    d = np.min([np.linalg.norm(np.cross(Q - a_, unit(b_ - a_)), axis=1) for a_, b_ in zip(pts[:-1], pts[1:])], axis=0)
    half[f] = float(np.median(d))
palm = COV[dom.get('Bip01 R Hand', [])]
mcp = np.mean([J[f][0] for f in FINGERS], 0)
G = mcp + f0 * 0.012 + n0 * (R_GRIP + 0.012)
AX = U
def _rad(p, c):
    v = p - c; return np.linalg.norm(v - np.outer(v @ AX, AX), axis=-1)
near = np.linalg.norm(palm - mcp, axis=1) < 0.075
for step in range(7):                                            # the thenar pad may stay against the shaft: a grip presses into it
    if _rad(palm[near], G).min() >= R_GRIP + 0.004: break
    G = G + n0 * 0.001
print('GRIP', np.round(G, 3), 'kn', np.round(kn, 3), 'U', np.round(U, 3), 'angle kn-U', round(math.degrees(math.acos(min(1.0, abs(kn @ U)))), 1), 'palm step mm', step, 'half cm', {k: round(v * 100, 2) for k, v in half.items()})


def radial(p):
    v = p - G; return np.linalg.norm(v - np.outer(v @ AX, AX), axis=-1)


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
        for t in (0.25, 0.5, 0.75, 1.0): s.append(a + (b - a) * t)
    return np.array(s)


tip0 = J['Middle'][3]
sg = 1.0 if ((rot(AX, 0.3) @ (tip0 - J['Middle'][0])) - (tip0 - J['Middle'][0])) @ n0 > 0 else -1.0
out = {}; posed = {}
for f in FINGERS:
    j = J[f]; best = None; want = R_GRIP + half[f] + 0.005
    for a1 in np.radians(np.arange(0, 96, 4)):
        for a2 in np.radians(np.arange(0, 111, 5)):
            for a3 in np.radians(np.arange(0, 81, 5)):
                if a3 > a2 + 1e-6: continue                     # anatomy: the fingertip joint bends no more than the middle one
                p = fk(j, (a1, a2, a3), sg); s_ = samples(p); r = radial(s_)
                c = ((r - want) ** 2).sum() + 400 * (np.minimum(r - (want - 0.001), 0) ** 2).sum()
                c += 0.0002 * ((a1 - a2) ** 2 + (a2 - 1.6 * a3) ** 2)   # share the curl: no joint folds on its own
                if best is None or c < best[0]: best = (c, (a1, a2, a3), p)
    out[f] = best[1]; posed[f] = best[2]
    print('FIST', f, np.round(np.degrees(best[1]), 0), 'r', np.round(radial(samples(best[2]))[[1, 5, 9, 11]], 3), 'want', round(want, 3), 'cost', round(best[0], 6))


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
target = posed['Middle'][2] + unit(posed['Middle'][2] - G) * (half['Middle'] + half['Thumb']) * 0.8   # the thumb closes over the middle finger, on the far side of the shaft
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
            if best is None or c < best[0]: best = (c, (R2, R3), (th, ph, ps), p3)
print('THUMB', np.round(np.degrees(best[2]), 0), 'tip to target', round(float(np.linalg.norm(best[3] - target)), 3))
grip.update(chain_pose('R', 'Thumb', [best[1][0], best[1][1], best[1][1]]))
json.dump(dict(grip=grip, relaxed={}, throw={}, hand_offset={'Bip01 R Hand': [Dloc.x, Dloc.y, Dloc.z, Dloc.w]}), open(POSES, 'w'), indent=0)

# --- move Xbase/Xmid onto the axis through G
xm0, xb0 = H('Xmid'), H('Xbase')
def to_axis(p):
    return G + U0 * ((p - G) @ U0)
L_mid = np.array([0.0])
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
Mi = np.linalg.inv(Wm)
for n, p in (('Xbase', to_axis(xb0)), ('Xmid', to_axis(xm0))):
    eb = rig.data.edit_bones[n]; d = Mi[:3, :3] @ (p - (xb0 if n == 'Xbase' else xm0))
    eb.head += Vector(d); eb.tail += Vector(d)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# --- half-joint helpers (corrective bones): each takes half its joint's rotation, keyed by helper_keys.py; the blend band goes torso -> helper -> limb, so skin in the band turns with the half
# rotation instead of collapsing between two full ones
HELP = [('Bip01 %s UpperArm', 'Bip01 %s UpperArm_H'), ('Bip01 %s Forearm', 'Bip01 %s Forearm_H'), ('Bip01 %s Thigh', 'Bip01 %s Thigh_H'), ('Bip01 %s Calf', 'Bip01 %s Calf_H')]
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for S in 'LR':
    for jn_, hn in HELP:
        j_ = eb[jn_ % S]; h_ = eb.new(hn % S)
        h_.head = j_.head.copy(); h_.tail = j_.tail.copy(); h_.roll = j_.roll; h_.parent = j_.parent; h_.use_connect = False; h_.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
for S in 'LR':
    for jn_, hn in HELP:
        body.vertex_groups.new(name=hn % S)
gi_ = {g.name: g.index for g in body.vertex_groups}
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
part = bm.faces.layers.int['part']
dvl = bm.verts.layers.deform.verify()
bm.verts.ensure_lookup_table()
# weights: helpers
moved = 0
for v in bm.verts:
    d_ = v[dvl]
    for S in 'LR':
        for jn_, hn in HELP:
            gj = gi_.get(jn_ % S)
            if gj is None or gj not in d_: continue
            w_ = d_[gj]
            if not 0.03 < w_ < 0.97: continue
            limb = jn_.split()[-1]
            child = {'UpperArm': 'Forearm', 'Thigh': 'Calf'}.get(limb)
            if child and d_.get(gi_.get(f'Bip01 {S} {child}', -1), 0.0) > 0: continue     # that band belongs to the child joint's helper
            up = {'Forearm': 'UpperArm', 'Calf': 'Thigh'}.get(limb)
            if up and d_.get(gi_.get(f'Bip01 {S} {up}', -1), 0.0) <= 0: continue          # the wrist and ankle bands are not this joint's
            others = {k: x for k, x in d_.items() if k != gj}
            tot = sum(others.values()) or 1.0
            hw = 1 - abs(2 * w_ - 1); jw = max(0.0, 2 * w_ - 1); ow = max(0.0, 1 - 2 * w_)
            for k, x in others.items(): d_[k] = x / tot * ow
            d_[gj] = jw; d_[gi_[hn % S]] = hw
            moved += 1
print('HELPER verts', moved)
# the bands get narrower when split in three: three smoothing passes over the helper verts, inside each garment, keep the fold spread
hset = {gi_[hn % S] for S in 'LR' for _, hn in HELP}
band = [v for v in bm.verts if any(k in hset and x > 0.001 for k, x in v[dvl].items())]
for it in range(3):
    new = {}
    for v in band:
        nb = [e.other_vert(v) for e in v.link_edges]
        acc = {k: 0.5 * x for k, x in v[dvl].items()}
        for u in nb:
            for k, x in u[dvl].items(): acc[k] = acc.get(k, 0.0) + 0.5 * x / len(nb)
        new[v] = acc
    for v, acc in new.items():
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; t_ = sum(x for _, x in top)
        v[dvl].clear()
        for k, x in top: v[dvl][k] = x / t_
# weights: the hem's inner wall follows the outer wall under it, vertex by vertex (no shear across the rolled hem)
sk = [v for f in bm.faces if f[part] == 7 for v in f.verts]
sk = list(set(sk))
for v in sk: v.normal_update()
outer = [v for v in sk if Vector((v.co.x, v.co.y, 0)).dot(v.normal) > 0]
inner = [v for v in sk if Vector((v.co.x, v.co.y, 0)).dot(v.normal) <= 0]
oc = np.array([tuple(v.co) for v in outer])
for v in inner:
    q = outer[int(np.argmin(((oc - np.array(tuple(v.co))) ** 2).sum(1)))]
    w0_ = dict(q[dvl].items()); v[dvl].clear()
    for k, x in w0_.items(): v[dvl][k] = x
print('HEM inner', len(inner), 'outer', len(outer))
# weights: the nape under the helmet, a wider Head/Neck blend at the back (the chin keeps its own plane)
gh, gn = gi_['Bip01 Head'], gi_['Bip01 Neck']
a_ = np.array([0, -0.06, 0.672]); b_ = np.array([0, 0.15, 0.70]); tv = unit(b_ - a_); nrm_ = np.cross(tv, [1, 0, 0]); nrm_ *= np.sign(nrm_[2])
for v in {v for f in bm.faces if f[part] == 2 for v in f.verts}:
    if v.co.y < 0.03: continue
    d0 = (np.array(tuple(v.co)) - a_) @ nrm_
    if abs(d0) > 0.05: continue
    t_ = np.clip((d0 + 0.05) / 0.10, 0, 1); wh_ = float(t_ * t_ * (3 - 2 * t_)); oth = v[dvl].get(gi_.get('Bip01 Spine2', -1), 0.0)
    v[dvl][gh] = wh_ * (1 - oth); v[dvl][gn] = (1 - wh_) * (1 - oth)
# weights: the coif (garm 16) hangs from the helmet: a long Head -> Neck ramp below the chin plane (7 cm below to 2 cm above) instead of
# the face's 3.6 cm band, Spine2 taking the share near the collar; the throat stretched 60 % of its faces when the head turned in the attack
gs2 = gi_['Bip01 Spine2']; garm = bm.faces.layers.int['garm']
for v in {v for f in bm.faces if f[garm] == 16 for v in f.verts}:
    d0 = (np.array(tuple(v.co)) - a_) @ nrm_
    t_ = np.clip((d0 + 0.07) / 0.09, 0, 1); wh_ = float(t_ * t_ * (3 - 2 * t_))
    ws_ = float((1 - wh_) * np.clip((0.64 - v.co.z) / 0.06, 0, 1) * 0.5)
    v[dvl].clear(); v[dvl][gh] = wh_; v[dvl][gs2] = ws_; v[dvl][gn] = 1 - wh_ - ws_
bm.to_mesh(me); bm.free()
# --- halberd placement (the attachment GLB is transformed by scripts/place_halberd.py)
Wv = unit(np.array([0.92496324, 0.36347082, 0.11104941]))
xm1 = to_axis(xm0)
Wv = RD.T @ Wv; Wv = unit(Wv - U * (Wv @ U)); Dv = np.cross(U, Wv)
tip_s = float((xm1 - G) @ U0 + (-0.534) + 0.22359444)
json.dump(dict(G=G.tolist(), U=U.tolist(), W=Wv.tolist(), D=Dv.tolist(), tip_s=tip_s, xbase=to_axis(xb0).tolist(), xmid=xm1.tolist()), open(os.path.join(HERE, 'work', 'halberd_place.json'), 'w'), indent=1)
print('HALBERD tip along U from the grip', round(tip_s, 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FINISH', len(me.polygons), 'tris')
