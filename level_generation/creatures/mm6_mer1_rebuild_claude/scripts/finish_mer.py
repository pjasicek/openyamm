"""After the paint (UVs frozen), on the rigged master (finish_thf.py adapted to the MM6 merchant's club; no body faces or UVs change):
- right fist solved round the club handle per finger, the thumb over them; a wrist turn lines the knuckles up with MM9's sword axis
  (`hand_offset`, applied with the grip by finger_keys_mer.py in every clip: the merchant always holds his club). Bone-local rotations in
  <hand poses json>.
- club: the approved MM6 club (mm6_mer1_club.glb, its local frame: grip centre at the origin, handle along +Y to the head) scaled with the body;
  Ybasesword moves to the grip (rest frame unchanged); work/club_place.json (Blender frame: grip G, axis U, across A) for place_club.py,
  which re-seats the club GLB in Ybasesword's bind frame. Args: <in blend> <out blend> <hand poses json>"""
import bpy, bmesh, sys, json, math, os
import numpy as np
from mathutils import Vector, Matrix
IN, OUT, POSES = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALE = json.load(open(os.path.join(HERE, 'work', 'clean_v1.json')))['scale']
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
Wm = np.array(rig.matrix_world)
H = lambda n: (Wm @ np.r_[np.array(rig.data.bones[n].head_local), 1])[:3]
BR = lambda n: Wm[:3, :3] @ np.array(rig.data.bones[n].matrix_local)[:3, :3]
unit = lambda v: v / np.linalg.norm(v)
def rot(ax, a): return np.array(Matrix.Rotation(a, 3, Vector(ax)))
DELTA = json.load(open(os.path.join(HERE, 'work', 'fit_v1.blend.delta.json')))
GJ = json.load(open(os.path.join(HERE, 'work', 'hands_v1.json')))['joints']
FN = {'Thumb': 1, 'Index': 2, 'Middle': 3, 'Ring': 4, 'Pinky': 5}
FINGERS = ('Index', 'Middle', 'Ring', 'Pinky')
gid = {g.index: g.name for g in body.vertex_groups}
dom = {}
for v in me.vertices:
    if v.groups:
        g = max(v.groups, key=lambda x: x.weight); dom.setdefault(gid[g.group], []).append(v.index)
COV = np.array([tuple(v.co) for v in me.vertices])
Z = np.load(os.path.join(HERE, 'work', 'club.npz'))
# the club in its own frame: t along the handle (grip -> head), a, b across; scaled with the body
DAG = {}
P = Z['P'] * SCALE
loc = np.c_[P[:, 1], P[:, 0], P[:, 2]]
tg = 0.02 * SCALE
near = np.abs(loc[:, 0] - tg) < 0.03
rg = float(np.percentile(np.hypot(loc[near, 1], loc[near, 2]), 70))
DAG['R'] = dict(loc=loc, tc=tg, r=rg)
print('CLUB length', round(float(np.ptp(loc[:, 0])), 3), 'grip t', round(tg, 3), 'grip r', round(rg, 4))
# MM9's weapon axes at MM9's rest, Blender coordinates, true-handed (mm9_highwayman_claude/scripts/finish_hw.py)
WEAP = {'R': dict(bone='Ybasesword', u=np.array([0.0, -1.0, -0.002]), a=np.array([-0.576, 0.002, -0.818]), kid=1),
        }
poses = dict(grip={}, relaxed={}, throw={}, hand_offset={})
placed = {}
for S, wp in WEAP.items():
    Dh = np.array(DELTA[f'Bip01 {S} Hand'])
    U0 = unit(Dh @ wp['u'])
    A0 = Dh @ wp['a']; A0 = unit(A0 - U0 * (A0 @ U0))
    J = {f: np.array([GJ[S][f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ[S][f'finger{k}-3_tip']]) for f, k in FN.items()}
    kn = unit(J['Index'][0] - J['Pinky'][0])
    f0 = unit(np.mean([J[f][1] - J[f][0] for f in FINGERS], 0)); f0 = unit(f0 - kn * (f0 @ kn))
    n0 = np.cross(kn, f0)
    if (np.mean([J[f][3] for f in FINGERS], 0) - np.mean([J[f][0] for f in FINGERS], 0)) @ n0 < 0: n0 = -n0
    v_ = np.cross(kn, U0); sn_ = np.linalg.norm(v_); th_ = math.atan2(sn_, kn @ U0)
    RD = rot(v_ / sn_, th_) if sn_ > 1e-6 else np.eye(3)
    BH = BR(f'Bip01 {S} Hand')
    Dloc = Matrix((BH.T @ RD @ BH).tolist()).to_quaternion()
    U = RD.T @ U0
    # a diagonal grip: the handle tilted TILT deg across the palm so the pommel end leaves the heel of the hand (held along MM9's sword
    # axis exactly, the handle behind the fist ran through the wrist skin when the club lines up with the forearm at the blow)
    TILT = math.radians(0.0)
    U = unit(U * math.cos(TILT) - unit(f0 - U * (f0 @ U)) * math.sin(TILT))
    Awv = unit(RD.T @ A0); Awv = unit(Awv - U * (Awv @ U)); B_ = np.cross(U, Awv)
    print('WRIST', S, 'turn deg', round(math.degrees(th_), 1), 'axis-knuckle now', round(math.degrees(math.acos(min(1, abs(kn @ U)))), 1))
    R_GRIP = DAG[S]['r']
    half = {}
    for f in FN:
        ids = sum((dom.get(f'Bip01 {S} {f}{i}', []) for i in (1, 2, 3)), [])
        Q = COV[ids]; pts = J[f]
        d = np.min([np.linalg.norm(np.cross(Q - a_, unit(b_ - a_)), axis=1) for a_, b_ in zip(pts[:-1], pts[1:])], axis=0)
        half[f] = float(np.median(d))
    palm = COV[dom.get(f'Bip01 {S} Hand', [])]
    mcp = np.mean([J[f][0] for f in FINGERS], 0)
    G = mcp + f0 * 0.012 + n0 * (R_GRIP + 0.012)
    AX = U
    def _rad(p, c):
        v = p - c; return np.linalg.norm(v - np.outer(v @ AX, AX), axis=-1)
    near = np.linalg.norm(palm - mcp, axis=1) < 0.075
    for step in range(9):
        if _rad(palm[near], G).min() >= R_GRIP + 0.004: break
        G = G + n0 * 0.001
    print('GRIP', S, np.round(G, 3), 'palm step mm', step, 'half cm', {k: round(v * 100, 2) for k, v in half.items()})
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
                    if a3 > a2 + 1e-6: continue
                    p = fk(j, (a1, a2, a3), sg); s_ = samples(p); r = radial(s_)
                    c = ((r - want) ** 2).sum() + 400 * (np.minimum(r - (want - 0.001), 0) ** 2).sum()
                    c += 0.0002 * ((a1 - a2) ** 2 + (a2 - 1.6 * a3) ** 2)
                    if best is None or c < best[0]: best = (c, (a1, a2, a3), p)
        out[f] = best[1]; posed[f] = best[2]
        print('FIST', S, f, np.round(np.degrees(best[1]), 0), 'r', np.round(radial(samples(best[2]))[[1, 5, 9, 11]], 3), 'want', round(want, 3), 'cost', round(best[0], 6))
    def chain_pose(f, deltas):
        res = {}; prev = np.eye(3)
        for i, D in enumerate(deltas):
            n = f'Bip01 {S} {f}{i + 1}'; Rb = BR(n)
            B = Rb.T @ prev.T @ D @ Rb
            q = Matrix(B.tolist()).to_quaternion()
            res[n] = [q.x, q.y, q.z, q.w]; prev = D
        return res
    for f in FINGERS:
        a1, a2, a3 = out[f]
        poses['grip'].update(chain_pose(f, [rot(AX, sg * a1), rot(AX, sg * (a1 + a2)), rot(AX, sg * (a1 + a2 + a3))]))
    t = J['Thumb']
    target = posed['Middle'][2] + unit(posed['Middle'][2] - G) * (half['Middle'] + half['Thumb']) * 0.8
    want = R_GRIP + half['Thumb'] + 0.005
    best = None
    for th in np.radians(np.arange(-120, 121, 5)):
        R1 = rot(f0, th)
        for ph in np.radians(np.arange(-100, 101, 5)):
            R2 = rot(AX, ph) @ R1
            for ps in np.radians(np.arange(0, 76, 6)):
                R3 = rot(AX, ps) @ R2
                p1 = t[0] + R2 @ (t[1] - t[0]); p2 = p1 + R3 @ (t[2] - t[1]); p3 = p2 + R3 @ (t[3] - t[2])
                s_ = samples(np.array([t[0], p1, p2, p3])); r = radial(s_)
                c = np.linalg.norm(p3 - target) + 60 * np.maximum(want - r, 0).sum()
                if best is None or c < best[0]: best = (c, (R2, R3), (th, ph, ps), p3)
    print('THUMB', S, np.round(np.degrees(best[2]), 0), 'tip to target', round(float(np.linalg.norm(best[3] - target)), 3))
    poses['grip'].update(chain_pose('Thumb', [best[1][0], best[1][1], best[1][1]]))
    poses['hand_offset'][f'Bip01 {S} Hand'] = [Dloc.x, Dloc.y, Dloc.z, Dloc.w]
    placed[S] = dict(G=G, U=U, A=Awv, B=B_)
json.dump(poses, open(POSES, 'w'), indent=0)
# weapon bones on the grip, rest rotation unchanged
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
Mi = np.linalg.inv(Wm)
for S, wp in WEAP.items():
    eb = rig.data.edit_bones[wp['bone']]; d = Mi[:3, :3] @ (placed[S]['G'] - H(wp['bone']))
    eb.head += Vector(d); eb.tail += Vector(d)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
P_ = placed['R']
# the native merchant (mer1sta*, mer1wa*) carries the club hanging head down at his right hip and draws it in the attack (mer1atb..atf):
# belt placement on the skirt's right side, behind the hip (angle TH_BELT from the back, x < 0: the right hand rests and swings at -130..-51 deg), pommel tucked under the belt, handle along the skirt's surface
TH_BELT = -40.0
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
sk = np.array(sorted({v for p in me.polygons if fp[p.index] == 7 for v in p.vertices})); SP = COV[sk]
th = np.degrees(np.arctan2(SP[:, 0], SP[:, 1]))
def surf(z):
    m = (np.abs(((th - TH_BELT + 180) % 360) - 180) < 12) & (np.abs(SP[:, 2] - z) < 0.04)
    return float(np.median(np.hypot(SP[m, 0], SP[m, 1])))
d = np.array([math.sin(math.radians(TH_BELT)), math.cos(math.radians(TH_BELT)), 0.0])
ztop, zbot = 0.05, -0.40
top = d * (surf(0.0) + 0.03) + np.array([0, 0, ztop]); bot = d * (surf(zbot) + 0.10) + np.array([0, 0, zbot])
Ub = unit(bot - top); Ab = unit(np.cross(Ub, d)); Gb = top + Ub * (0.067 * SCALE + DAG['R']['tc'])
json.dump(dict(G=P_['G'].tolist(), U=P_['U'].tolist(), A=P_['A'].tolist(), B=P_['B'].tolist(), tc=DAG['R']['tc'], scale=SCALE,
               ybase=H('Ybasesword').tolist(), belt=dict(G=Gb.tolist(), U=Ub.tolist(), A=Ab.tolist()), hand=H('Bip01 R Hand').tolist()),
          open(os.path.join(HERE, 'work', 'club_place.json'), 'w'), indent=1)
print('BELT club grip', Gb.round(3), 'axis', Ub.round(3))
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.new('Club'); eb.head = Vector((Mi @ np.r_[Gb, 1])[:3]); eb.tail = Vector((Mi @ np.r_[Gb + Ub * 0.1, 1])[:3])
# the club lies on the robe: it rides on the top bone of the robe column nearest its angle (it swings with the skirt)
kcol = int(round((TH_BELT + 180 - 11.25) / 22.5)) % 16
eb.parent = rig.data.edit_bones[f'Robe_{kcol:02d}_0']; eb.use_connect = False; eb.use_deform = True
print('CLUB parent', eb.parent.name)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FINISH', len(me.polygons), 'tris', 'club grip r', round(DAG['R']['r'], 4))
