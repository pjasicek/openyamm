"""(mm9_giant_claude/scripts/fist_giant.py, read and copied 2026-10-31, for Yanmir's staff) Right fist round the staff's shaft (from mm9_highwayman_claude/scripts/finish_hw.py, fist part; frames from the graft json).
MM9's handle axis stays fixed in the right hand's frame in every clip (turn <= 2.8 deg, offset <= 2.1 cm, measured), sliding along
itself only, so one grip pose holds everywhere. Fingers solved round the axis per finger, the thumb over them; a constant wrist
turn lines the knuckles up with MM9's axis; the mallet is placed turned back by it about the grip so it still points where MM9's
points, and Xbase / Xhammer move to the grip (rest rotations unchanged). Bone-local rotations go to work/hand_poses.json
(finger_keys.py). Writes the mallet (work/mallet.npz) into the body: vertex attribute part 20, face attribute mat 3, rigid on
Ystaff, UVs in PartUV. Args: <in blend> <out blend> <hand poses json>"""
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
BR = lambda n: Wm[:3, :3] @ np.array(rig.data.bones[n].matrix_local)[:3, :3]
unit = lambda v: v / np.linalg.norm(v)
def rot(ax, a): return np.array(Matrix.Rotation(a, 3, Vector(ax)))
GJ = json.load(open(os.path.join(HERE, 'work', 'hands_v1.json')))['joints']
MZ = np.load(os.path.join(HERE, 'work', 'staff.npz'))
# the staff's frame on OUR rest: MM9's Ystaff frame turned by the right hand's rest turn (rig_yan.py), at the moved Ystaff joint
DL = json.load(open(os.path.join(HERE, 'work', 'rig_v1.blend.delta.json')))
M = np.array(MZ['M']); M[:3, :3] = np.array(DL['Ystaff']) @ M[:3, :3]; M[:3, 3] = H('Ystaff')
AXm = unit(M[:3, 1]); Om = M[:3, 3]           # the shaft axis (Ystaff local +y) and Ystaff's origin, Blender, our rest
FN = {'Thumb': 1, 'Index': 2, 'Middle': 3, 'Ring': 4, 'Pinky': 5}
FINGERS = ('Index', 'Middle', 'Ring', 'Pinky')
gid = {g.index: g.name for g in body.vertex_groups}
dom = {}
for v in me.vertices:
    if v.groups:
        g = max(v.groups, key=lambda x: x.weight); dom.setdefault(gid[g.group], []).append(v.index)
COV = np.array([tuple(v.co) for v in me.vertices])
R_GRIP = float(os.environ.get('R_GRIP', '0.037'))      # the follow-up's thick pole at the grip: r 0.036-0.038 (make_staff.py)
KO = float(os.environ.get('KO', '0.02'))              # offsets: this hand is about 1.5 x the highwayman's
poses = dict(grip={}, relaxed={}, hand_offset={})
S = 'R'
J = {f: np.array([GJ[S][f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ[S][f'finger{k}-3_tip']]) for f, k in FN.items()}
kn = unit(J['Index'][0] - J['Pinky'][0])
f0 = unit(np.mean([J[f][1] - J[f][0] for f in FINGERS], 0)); f0 = unit(f0 - kn * (f0 @ kn))
n0 = np.cross(kn, f0)
if (np.mean([J[f][3] for f in FINGERS], 0) - np.mean([J[f][0] for f in FINGERS], 0)) @ n0 < 0: n0 = -n0
U0 = AXm if AXm @ kn > 0 else -AXm
v_ = np.cross(kn, U0); sn_ = np.linalg.norm(v_); th_ = math.atan2(sn_, kn @ U0)
RD = rot(v_ / sn_, th_) if sn_ > 1e-6 else np.eye(3)
BH = BR(f'Bip01 {S} Hand')
Dloc = Matrix((BH.T @ RD @ BH).tolist()).to_quaternion()
U = RD.T @ U0
print('WRIST', S, 'turn deg', round(math.degrees(th_), 1), 'n0', np.round(n0, 3), 'kn', np.round(kn, 3), 'f0', np.round(f0, 3), 'mcp', np.round(np.mean([J[f][0] for f in FINGERS], 0), 3))
half = {}
for f in FN:
    ids = sum((dom.get(f'Bip01 {S} {f}{i}', []) for i in (1, 2, 3)), [])
    Q = COV[ids]; pts = J[f]
    d = np.min([np.linalg.norm(np.cross(Q - a_, unit(b_ - a_)), axis=1) for a_, b_ in zip(pts[:-1], pts[1:])], axis=0)
    half[f] = float(np.median(d))
palm = COV[dom.get(f'Bip01 {S} Hand', [])]
mcp = np.mean([J[f][0] for f in FINGERS], 0)
# fixed fist curls about the knuckle line (each finger's own flexion), tried on the skinned mesh in Blender: for each, the fist's
# free hole across the knuckle line is searched (outside the skin by the nearest face's normal, surrounded by the hand's
# vertices with no angular gap over 100 deg); the curl whose hole is closest to the handle radius + 3 mm wins, the handle runs
# through the hole's centre.
from mathutils.bvhtree import BVHTree
AX = U
CF = json.load(open(os.path.join(HERE, 'scripts', 'graft_yan.json')))['sides'][S]
npm = np.array(CF['n_dir']); npm = unit(npm - AX * (npm @ AX)); e2 = unit(np.cross(AX, npm))
tip0 = J['Middle'][3]
hp_ = np.array(CF['h_dir']); hp_ = unit(hp_ - AX * (hp_ @ AX))
heel = J['Middle'][0] + npm * 0.05 - hp_ * 0.08
dd = lambda a: np.linalg.norm(J['Middle'][0] + rot(AX, a) @ (tip0 - J['Middle'][0]) - heel)
sg = 1.0 if dd(0.5) < dd(-0.5) else -1.0
def chain_pose(f, deltas):
    res = {}; prev = np.eye(3)
    for i, D in enumerate(deltas):
        n = f'Bip01 {S} {f}{i + 1}'; Rb = BR(n)
        B = Rb.T @ prev.T @ D @ Rb
        q = Matrix(B.tolist()).to_quaternion()
        res[n] = [q.x, q.y, q.z, q.w]; prev = D
    return res
hand_bones = [b.name for b in rig.data.bones if f' {S} ' in b.name and any(k in b.name for k in ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
def posed_hole(grip):
    for pb in rig.pose.bones: pb.matrix_basis.identity(); pb.rotation_mode = 'QUATERNION'
    for n, q in grip.items(): rig.pose.bones[n].rotation_quaternion = (q[3], q[0], q[1], q[2])
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); em = ev.to_mesh()
    Pp = np.array([tuple(body.matrix_world @ v.co) for v in em.vertices])
    tris = [tuple(p.vertices) for p in em.polygons]
    bvh = BVHTree.FromPolygons([Vector(p) for p in Pp], tris)
    ev.to_mesh_clear()
    gi = {g.index: g.name for g in body.vertex_groups}
    hv = np.array([v.index for v in me.vertices if v.groups and gi[max(v.groups, key=lambda x: x.weight).group] in hand_bones])
    HP = Pp[hv]; cen = HP.mean(0)
    best = None
    for du in np.arange(-0.10, 0.101, 0.004):
        for dv in np.arange(-0.04, 0.141, 0.004):
            G = mcp + e2 * du + npm * dv
            loc, nor, _, dist = bvh.find_nearest(Vector(G))
            if loc is None or (G - np.array(loc)) @ np.array(nor) < 0: continue
            q = HP - G; al = q @ AX; sl = np.abs(al) < 0.04; q = q[sl] - np.outer(al[sl], AX)
            r = np.linalg.norm(q, axis=1); near = r < 0.10
            if near.sum() < 10: continue
            ang = np.sort(np.arctan2(q[near] @ npm, q[near] @ e2))
            gap = np.degrees(np.max(np.diff(np.r_[ang, ang[0] + 2 * np.pi])))
            if gap > 100: continue
            if best is None or dist > best[0]: best = (dist, G, gap, du, dv)
    for pb in rig.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    return best
mcp = np.mean([J[f][0] for f in FINGERS], 0)
# Yanmir (r4): each finger wraps the same cylinder with its own curl (fist_giant.py's one curl for all four fingers and its
# empty-point hole put the shaft through the proximal phalanges: the pinky is shorter and closes inside the others' circle).
# A grid of centres G in front of the knuckles across the curl axis; per G and finger the MCP/PIP/DIP angles from a grid
# that keep the phalanx lines tangent to the circle of radius R_GRIP + 2 mm + that finger's half thickness (penalty inside it);
# the palm line (wrist -> knuckles) must stay R_GRIP + 1.5 cm clear. Least total cost wins.
pe1 = unit(np.cross(AX, npm)); pe2 = unit(np.cross(AX, pe1))
Wr0 = H('Bip01 R Hand')
P2 = lambda p: np.array([(p - mcp) @ pe1, (p - mcp) @ pe2])
def seg2(p, a_, b_):
    ab = b_ - a_; t = np.clip(((p - a_) @ ab) / max(ab @ ab, 1e-12), 0, 1); return np.linalg.norm(p - a_ - t[..., None] * ab, axis=-1)
def rot2(v, a):
    c, s_ = np.cos(a), np.sin(a); return np.stack([c * v[0] - s_ * v[1], s_ * v[0] + c * v[1]], -1)
A1 = np.radians(np.arange(-10, 80, 5)); A2 = np.radians(np.arange(-10, 105, 5)); A3 = np.radians(np.arange(-10, 75, 10))      # MPFB's rest already curls the fingers: a thick pole may need less PIP flex
g1, g2, g3 = [x.ravel() for x in np.meshgrid(A1, A2, A3, indexing='ij')]
JF = {f: [P2(p) for p in J[f]] for f in FINGERS}
PAD = float(os.environ.get('PAD', '0.006'))      # the palm-side pads and the knuckle webbing bulge past the median half thickness (r4 at 2 mm: 0.9-1.4 cm in the shaft)
def fit_finger(f, Gc, k):
    j = JF[f]; R_ = R_GRIP + PAD + half[f]
    v0, v1, v2 = j[1] - j[0], j[2] - j[1], j[3] - j[2]
    p0 = np.repeat(j[0][None], len(g1), 0)
    p1 = p0 + rot2(v0, sg * g1); p2 = p1 + rot2(v1, sg * (g1 + g2)); p3 = p2 + rot2(v2, sg * (g1 + g2 + g3))
    cost = 0
    for a_, b_ in ((p0, p1), (p1, p2), (p2, p3)):
        for t in (0.25, 0.5, 0.75, 1.0):
            d = np.linalg.norm(a_ + (b_ - a_) * t - Gc, axis=1)
            cost = cost + np.abs(d - R_) + 8 * np.maximum(R_ - d, 0)
    i = int(np.argmin(cost)); return float(cost[i]), (g1[i], g2[i], g3[i])
pl = P2(Wr0)
best = None
for u in np.arange(-0.06, 0.061, 0.004):
    for v in np.arange(-0.10, 0.021, 0.004):
        Gc = np.array([u, v])
        if seg2(Gc[None], pl, np.zeros(2))[0] < R_GRIP + 0.015: continue
        tot = 4 * abs(seg2(Gc[None], pl, np.zeros(2))[0] - (R_GRIP + 0.018)); angs = {}      # the pole lies in the palm (palm half thickness 1.8 cm)
        for f in FINGERS:
            c_, a_ = fit_finger(f, Gc, 0); tot += c_; angs[f] = a_
        if best is None or tot < best[0]: best = (tot, Gc, angs)
_, G2c, ANG = best
G = mcp + pe1 * G2c[0] + pe2 * G2c[1] + AX * float(np.mean([(J[f][0] - mcp) @ AX for f in FINGERS]))
grip = {}; posed = {}
for f in FINGERS:
    a1, a2, a3 = ANG[f]; j = J[f]
    grip.update(chain_pose(f, [rot(AX, sg * a1), rot(AX, sg * (a1 + a2)), rot(AX, sg * (a1 + a2 + a3))]))
    p1 = j[0] + rot(AX, sg * a1) @ (j[1] - j[0]); p2 = p1 + rot(AX, sg * (a1 + a2)) @ (j[2] - j[1]); p3 = p2 + rot(AX, sg * (a1 + a2 + a3)) @ (j[3] - j[2])
    posed[f] = np.array([j[0], p1, p2, p3])
poses['grip'].update(grip)
R_HOLE = R_GRIP
if os.environ.get('DBG'): np.savez(os.path.join(HERE, 'work', 'fist_dbg_t.npz'), thumb=np.array([P2(p) for p in J['Thumb']])); np.savez(os.path.join(HERE, 'work', 'fist_dbg.npz'), G=G2c, pl=pl, R=np.array([R_GRIP + PAD + half[f] for f in FINGERS]), rest=np.array([[P2(p) for p in J[f]] for f in FINGERS]), posed=np.array([[P2(p) for p in posed[f]] for f in FINGERS]))
print('GRIP', S, 'per finger deg', {f: [int(round(np.degrees(x))) for x in ANG[f]] for f in FINGERS}, 'cost', round(best[0], 3), 'G2 cm', np.round(G2c * 100, 1), 'half cm', {f: round(v * 100, 2) for f, v in half.items()})
def radial(p):
    v = p - G; return np.linalg.norm(v - np.outer(v @ AX, AX), axis=-1)
def samples(pts):
    s = []
    for a, b in zip(pts[:-1], pts[1:]):
        for t in (0.25, 0.5, 0.75, 1.0): s.append(a + (b - a) * t)
    return np.array(s)
t = J['Thumb']
# follow-up: the thumb closes OVER the shaft (r4 left it beside it, 15 deg wrap): its tip on the index finger's middle phalanx, outside,
# and its two distal segments lying on the pole (radial distance near the pole radius + its half thickness)
radial_out = lambda p: unit((p - G) - AX * ((p - G) @ AX))
pip = posed['Index'][2] + 0.6 * (posed['Index'][3] - posed['Index'][2])      # over the index finger's last phalanx, where the fingers end
target = pip + radial_out(pip) * (half['Index'] + half['Thumb']) * 0.9
want = R_GRIP + half['Thumb'] + 0.004
best = None
for th in np.radians(np.arange(-180, 180, 6)):
    R1 = rot(f0, th)
    for ph in np.radians(np.arange(-180, 180, 6)):
        R2 = rot(AX, ph) @ R1
        for ps in np.radians(np.arange(-30, 76, 8)):
            R3 = rot(AX, ps) @ R2
            p1 = t[0] + R2 @ (t[1] - t[0]); p2 = p1 + R3 @ (t[2] - t[1]); p3 = p2 + R3 @ (t[3] - t[2])
            s_ = samples(np.array([t[0], p1, p2, p3])); r = radial(s_)
            rd = radial(samples(np.array([p1, p2, p3])))
            c = np.linalg.norm(p3 - target) + 0.15 * np.abs(rd - want).mean() + 60 * np.maximum(want - r, 0).sum()
            if best is None or c < best[0]: best = (c, (R2, R3), (th, ph, ps), p3)
print('THUMB', S, np.round(np.degrees(best[2]), 0), 'tip to target', round(float(np.linalg.norm(best[3] - target)), 3))
if os.environ.get('DBG'): np.savez(os.path.join(HERE, 'work', 'fist_dbg_t.npz'), thumb=np.array([P2(p) for p in J['Thumb']]), target=P2(target), tip=P2(best[3]))
poses['grip'].update(chain_pose('Thumb', [best[1][0], best[1][1], best[1][1]]))
poses['hand_offset'][f'Bip01 {S} Hand'] = [Dloc.x, Dloc.y, Dloc.z, Dloc.w]
# left hand: flexion frame for finger_keys_giant.py (curl amounts from MM9's left finger joints per frame)
JL = {f: np.array([GJ['L'][f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ['L'][f'finger{k}-3_tip']]) for f, k in FN.items()}
knL = unit(JL['Index'][0] - JL['Pinky'][0])
CFL = json.load(open(os.path.join(HERE, 'scripts', 'graft_yan.json')))['sides']['L']
npL = np.array(CFL['n_dir']); npL = unit(npL - knL * (npL @ knL)); hpL = np.array(CFL['h_dir']); hpL = unit(hpL - knL * (hpL @ knL))
heelL = JL['Middle'][0] + npL * 0.05 - hpL * 0.08
ddL = lambda a: np.linalg.norm(JL['Middle'][0] + rot(knL, a) @ (JL['Middle'][3] - JL['Middle'][0]) - heelL)
sgL = 1.0 if ddL(0.5) < ddL(-0.5) else -1.0
poses['flexL'] = {'AX': knL.tolist(), 'sg': sgL, 'Rb': {b.name: BR(b.name).tolist() for b in rig.data.bones if b.name.startswith('Bip01 L ') and any(k in b.name for k in FINGERS)}}
print('FLEXL sg', sgL, 'kn', np.round(knL, 3))
json.dump(poses, open(POSES, 'w'), indent=0)
# staff: MM9's, unrotated, shifted so its axis runs through the fist's hole AFTER the wrist turn (G' = the grip turned by RD about
# the wrist). finger_keys_yan.py takes the wrist turn back out of Ystaff's keys, so the staff keeps MM9's own axis.
Wr = H(f'Bip01 {S} Hand')
G2 = Wr + RD @ (G - Wr)
W0 = MZ['V'] @ M[:3, :3].T + M[:3, 3]
Gm = Om + AXm * ((G2 - Om) @ AXm); D = G2 - Gm
Pw = W0 + D
print('STAFF shift cm', np.round(D * 100, 2), 'grip along handle', round(float((G2 - Om) @ AXm), 3))
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
Mi = np.linalg.inv(Wm)
for nm in ('Ystaff', 'Ystafftop', 'Ystaffbot'):
    eb = rig.data.edit_bones[nm]; d = Mi[:3, :3] @ D; eb.head += Vector(d); eb.tail += Vector(d)
bpy.ops.object.mode_set(mode='OBJECT')
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.verts.layers.int['part']; dv = bm.verts.layers.deform.verify()
gi = body.vertex_groups.find('Ystaff')
if gi < 0: gi = body.vertex_groups.new(name='Ystaff').index
nv = [bm.verts.new(p.tolist()) for p in Pw]
for x in nv: x[lay] = 20; x[dv][gi] = 1.0
uvl = bm.loops.layers.uv.get('PartUV'); mt = bm.faces.layers.int.get('mat')
flip = np.linalg.det(M[:3, :3]) < 0
for f in MZ['F']:
    tri = (f[0], f[2], f[1]) if flip else tuple(f)
    try:
        q = bm.faces.new([nv[i] for i in tri]); q.smooth = False
    except ValueError: continue
    if uvl is not None:
        for l, i in zip(q.loops, tri): l[uvl].uv = (float(MZ['UV'][i, 0]), float(MZ['UV'][i, 1]))
    if mt is not None: q[mt] = 3
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FISTDONE')
