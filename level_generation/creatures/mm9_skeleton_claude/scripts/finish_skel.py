"""After the paint (UVs frozen), geometry that shares existing texels, on the rigged master (from finish_skelwar.py):
- lining: the vest panels, strap, back panel and hip scraps are single sheets, so a view of their inside showed the background (back faces are culled in game).
  Each gets a coincident inner copy, flipped, same weights, on one dark texel of the body set.
- dagger (work/dagger_mesh.npz): rigid on Bone01, moved to the handle axis in the fist, faces with attribute `scim`. The handle lies along MM9's handle direction, the blade in MM9's
  blade plane, and the knuckle line is on that handle (fit_skel).
- fist: the fingers are solved round the handle cylinder per finger on a grid, the thumb over them. Poses are bone-local rotations in work/hand_poses.json, keyed by finger_keys.py:
  grip (R), relaxed and clench (L).
Args: <in blend> <out blend> <hand poses json>"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
IN, OUT, POSES = sys.argv[sys.argv.index('--') + 1:]
MID = 0.0
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
W = np.array(rig.matrix_world)
H = lambda n: (W @ np.r_[np.array(rig.data.bones[n].head_local), 1])[:3]
T = lambda n: (W @ np.r_[np.array(rig.data.bones[n].tail_local), 1])[:3]
BR = lambda n: W[:3, :3] @ np.array(rig.data.bones[n].matrix_local)[:3, :3]
unit = lambda v: v / np.linalg.norm(v)
FINGERS = ('Index', 'Middle', 'Ring', 'Pinky')
LAST = lambda f: 2 if f == 'Thumb' else 3
ch = lambda s, f: np.array([H(f'Bip01 {s} {f}{i}') for i in range(1, LAST(f) + 1)] + [T(f'Bip01 {s} {f}{LAST(f)}')])


def rot(ax, a):
    return np.array(Matrix.Rotation(a, 3, Vector(ax)))


# --- grip
J = {f: ch('R', f) for f in FINGERS + ('Thumb',)}
kn = unit(J['Index'][0] - J['Pinky'][0])
f0 = unit(np.mean([J[f][1] - J[f][0] for f in FINGERS], 0)); f0 = unit(f0 - kn * (f0 @ kn))
n0 = np.cross(kn, f0)
if (np.mean([J[f][3] for f in FINGERS], 0) - np.mean([J[f][0] for f in FINGERS], 0)) @ n0 < 0:
    print('palm normal flipped'); n0 = -n0
R_GRIP, FR = 0.0105, 0.0075
mcp = np.mean([J[f][0] for f in FINGERS], 0)
G = mcp + f0 * 0.030 + n0 * (R_GRIP + FR + 0.003)
print('GRIP', np.round(G, 3), 'kn', np.round(kn, 3), 'f', np.round(f0, 3), 'n', np.round(n0, 3))
AX = kn


def radial(p):
    v = p - G; return np.linalg.norm(v - np.outer(v @ AX, AX), axis=-1)


def fk(j, angs, sign):
    pts = [j[0]]; R = np.eye(3); total = 0.0
    p = j[0]
    for i, a in enumerate(angs):
        total += a
        R = rot(AX, sign * total)
        p = p + R @ (j[i + 1] - j[i])
        pts.append(p)
    return np.array(pts)


def samples(pts):
    s = []
    for a, b in zip(pts[:-1], pts[1:]):
        for t in (0.25, 0.5, 0.75, 1.0): s.append(a + (b - a) * t)
    return np.array(s)


# flex sign: a positive curl moves the fingertip toward the palm normal
tip0 = J['Middle'][3]
sg = 1.0 if ((rot(AX, 0.3) @ (tip0 - J['Middle'][0])) - (tip0 - J['Middle'][0])) @ n0 > 0 else -1.0
out = {}; posed = {}
for f in FINGERS:
    j = J[f]; best = None
    for a1 in np.radians(np.arange(0, 96, 4)):
        for a2 in np.radians(np.arange(0, 111, 5)):
            for a3 in np.radians(np.arange(0, 91, 5)):
                p = fk(j, (a1, a2, a3), sg); s = samples(p); r = radial(s)
                c = ((r - (R_GRIP + FR)) ** 2).sum() + 20 * (np.minimum(r - (R_GRIP + FR - 0.002), 0) ** 2).sum()
                # the tip comes back toward the palm: reward wrapping
                wrap = (p[3] - G) @ n0
                c += 0.002 * max(0.0, wrap + 0.012) * 10
                if best is None or c < best[0]: best = (c, (a1, a2, a3), p)
    out[f] = best[1]; posed[f] = best[2]
    print('FIST', f, np.round(np.degrees(best[1]), 0), 'r', np.round(radial(samples(best[2]))[[1, 5, 9, 11]], 3), 'cost', round(best[0], 6))


def chain_pose(s, f, deltas):
    """bone-local rotations from world deltas of each bone (relative to the hand)."""
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
# thumb: swing about the finger direction, curl about the handle, tip onto the index's middle segment
t = J['Thumb']
target = posed['Index'][2] + unit(posed['Index'][2] - G) * 0.012 - f0 * 0.0
best = None
for th in np.radians(np.arange(-30, 91, 6)):
    R1 = rot(f0, th)
    for ph in np.radians(np.arange(-60, 91, 6)):
        R2 = rot(AX, ph) @ R1
        for ps in np.radians(np.arange(0, 76, 8)):
            R3 = rot(AX, ps) @ R2
            p1 = t[0] + R2 @ (t[1] - t[0]); p3 = p1 + R3 @ (t[2] - t[1])
            s = samples(np.array([t[0], p1, p3])); r = radial(s)
            c = np.linalg.norm(p3 - target) + 3 * np.maximum(R_GRIP + 0.007 - r, 0).sum()
            if best is None or c < best[0]: best = (c, (R2, R3), (th, ph, ps), p3)
print('THUMB', np.round(np.degrees(best[2]), 0), 'tip to target', round(np.linalg.norm(best[3] - target), 3))
grip.update(chain_pose('R', 'Thumb', [best[1][0], best[1][1]]))
# left hand: mirror axes
JL = {f: ch('L', f) for f in FINGERS + ('Thumb',)}
S = np.diag([-1.0, 1, 1])
axL = S @ AX
sL = -sg


def curl(s, ax, sign, a, thumb):
    res = {}
    for f in FINGERS:
        res.update(chain_pose(s, f, [rot(ax, sign * a[0]), rot(ax, sign * (a[0] + a[1])), rot(ax, sign * (a[0] + a[1] + a[2]))]))
    res.update(chain_pose(s, 'Thumb', [rot(ax, sign * thumb[0]), rot(ax, sign * (thumb[0] + thumb[1]))]))
    return res


relaxed = curl('L', axL, sL, np.radians((24, 30, 16)), np.radians((8, 10)))
throw = curl('L', axL, sL, np.radians((62, 72, 45)), np.radians((25, 25)))
json.dump(dict(grip=grip, relaxed=relaxed, throw=throw), open(POSES, 'w'), indent=0)

# --- lining + hips
bm = bmesh.new(); bm.from_mesh(me)
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
# spikes: the decimation left a few needle vertices on gauntlets and bones (a 4 cm thorn beside the pinky). The UVs stay; such a
# vertex goes back to the middle of its neighbours (armour edges and the skirt's points are real and not touched)
pl0 = bm.verts.layers.int['pid']
SMOOTH = {18, 36, 65, 30, 44, 76}; SMOOTH |= {p + 1000 for p in SMOOTH}
total = 0
for it in range(3):
    moved = 0
    for v in bm.verts:
        if v[pl0] not in SMOOTH or not v.link_edges: continue
        nb = [e.other_vert(v) for e in v.link_edges]
        c = sum((x.co for x in nb), Vector()) / len(nb)
        off = (v.co - c).length
        ring = sorted((a.co - b.co).length for i, a in enumerate(nb) for b in nb[i + 1:])
        if off > 0.012 and off > 1.6 * ring[len(ring) // 2]:
            v.co = c; moved += 1
    total += moved
print('SPIKES moved', total)
# two toe bones came out of uv_atlas with zero-area UVs (flat beige in the viewer): they borrow the texels of the toe bone beside them, vertex by nearest vertex
uvb0 = bm.loops.layers.uv['UVMap']; pl4 = bm.verts.layers.int['pid']
for dst, src in ((79, 105), (133, 101), (1079, 105), (1133, 101)):
    dv = [v for v in bm.verts if v[pl4] == dst]; sv = [v for v in bm.verts if v[pl4] == src]
    dc = np.array([tuple(v.co) for v in dv]); sc_ = np.array([tuple(v.co) for v in sv])
    suv = np.array([tuple(l[uvb0].uv) for v in sv for l in v.link_loops]); lo_, hi_ = np.percentile(suv, 25, axis=0), np.percentile(suv, 75, axis=0)     # the middle of the neighbour's chart
    dc = dc - dc.mean(0); a0, a1 = np.argsort(np.ptp(dc, axis=0))[::-1][:2]             # planar: longest and second axis
    pu = (dc[:, a0] - dc[:, a0].min()) / max(np.ptp(dc[:, a0]), 1e-6); pv = (dc[:, a1] - dc[:, a1].min()) / max(np.ptp(dc[:, a1]), 1e-6)
    for v, u_, v_ in zip(dv, pu, pv):
        uv_ = Vector((lo_[0] + (hi_[0] - lo_[0]) * u_, lo_[1] + (hi_[1] - lo_[1]) * v_))
        for l in v.link_loops: l[uvb0].uv = uv_
print('SPIKES toe UVs borrowed')
# eyes: on the socket floor they broke through the thin temple (a green dot on the side of the skull): forward and inward into the orbit
pl3 = bm.verts.layers.int['pid']
for v in bm.verts:
    if v[pl3] == 2002: v.co += Vector((0.007, -0.017, 0.0))
    elif v[pl3] == 2003: v.co += Vector((-0.007, -0.017, 0.0))
# sheets the wrong way round (the back panel was built facing in): each torso sheet's outer face away from the spine; the loops keep their UVs
pl2 = bm.verts.layers.int['pid']
for p_ in (52, 144, 1052, 1144):                          # closed slivers Meshy returned inside out
    fs = [f for f in bm.faces if f.verts[0][pl2] == p_]
    bmesh.ops.reverse_faces(bm, faces=fs)
for p_ in (2, 47, 1002, 1047, 14, 124, 300):
    fs = [f for f in bm.faces if f.verts[0][pl2] == p_]
    bm.normal_update()
    d = sum((f.calc_area() * f.normal.dot((f.calc_center_median() - Vector((0, 0.06, f.calc_center_median().z))).normalized()) for f in fs))
    print('SPIKES sheet', p_, len(fs), 'outward' if d > 0 else 'FLIPPED')
    if d < 0: bmesh.ops.reverse_faces(bm, faces=fs)
# hip scraps: clear of the femur at rest (Meshy left them on it) and rigid on the thigh; the UVs stay
pl1 = bm.verts.layers.int['pid']; dfm0 = bm.verts.layers.deform.active
SCR0 = [52, 142, 134, 109, 144, 127]; nm0 = [g.name for g in body.vertex_groups]
sp0 = nm0.index('Bip01 Spine')
for s_, off_ in (('R', 0), ('L', 1000)):
    hip = H(f'Bip01 {s_} Thigh'); ax_ = unit(H(f'Bip01 {s_} Calf') - hip)
    bm.normal_update()
    fvs = [v for v in bm.verts if v[pl1] in (3 + off_, 65 + off_)]
    fv_co = np.array([tuple(v.co) for v in fvs]); fv_no = np.array([tuple(v.normal) for v in fvs])
    fv = fv_co
    tf = (fv - hip) @ ax_; rf = np.linalg.norm(fv - hip - np.outer(tf, ax_), axis=1)
    bins = np.arange(tf.min(), tf.max() + 0.03, 0.03); Rb = np.array([rf[(tf >= b) & (tf < b + 0.05)].max() if ((tf >= b) & (tf < b + 0.05)).any() else 0.0 for b in bins])
    th0 = nm0.index(f'Bip01 {s_} Thigh')
    for p_ in SCR0:
        vs = [v for v in bm.verts if v[pl1] == p_ + off_]
        q = np.array([tuple(v.co) for v in vs]) - hip; t_ = q @ ax_; rd = q - np.outer(t_, ax_); r_ = np.linalg.norm(rd, axis=1)
        dir_ = unit(rd.mean(0)); push = 0.0
        pts_ = np.array([tuple(v.co) for v in vs])
        for push in np.arange(0.0, 0.031, 0.003):              # the least rigid shift that takes the strip out of the femur: it rides with the thigh, so that is all it needs
            d_v = np.linalg.norm((pts_ + dir_ * push)[:, None] - fv_co[None], axis=2); nn = d_v.argmin(1)
            if not (((pts_ + dir_ * push - fv_co[nn]) * fv_no[nn]).sum(1) < -0.001).any(): break
        for v in vs:
            v.co += Vector(dir_ * push)
            for k in list(v[dfm0].keys()): del v[dfm0][k]
            v[dfm0][th0] = 1.0                  # rigid on the thigh: any blend from the belt folded them (collapse gate) or let the femur through (scrap_gate)
        print('SPIKES scrap', p_ + off_, 'push cm', round(push * 100, 1))
print('SPIKES scraps pushed')
lin = bm.faces.layers.int.new('lining'); scl = bm.faces.layers.int.new('scim')
pidl = bm.verts.layers.int['pid']; uvb = bm.loops.layers.uv['UVMap']; uvh = bm.loops.layers.uv['HeadUV']
headl = bm.faces.layers.int['head']
SCR = [142, 134, 109, 127]                                  # 52, 144 and 124 are closed thin solids, they need no lining (a reversed copy of a closed part is an inverted part)
LIN = {2, 47, 14, 300} | set(SCR) | {p + 1000 for p in [2, 47] + SCR}


def dark_uv(path, faces, layer):
    img = bpy.data.images.load(path, check_existing=True)
    h, w = img.size[1], img.size[0]; px = np.empty(h * w * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(h, w, 4)
    cs = []
    for f in faces:
        c = sum((np.array(tuple(l[layer].uv)) for l in f.loops), np.zeros(2)) / 3
        cs.append((px[min(h - 1, int(c[1] * h)), min(w - 1, int(c[0] * w)), :3] @ [.3, .6, .1], tuple(c)))
    cs.sort(key=lambda x: x[0])
    return cs[len(cs) * 3 // 4][1]


fb = [f for f in bm.faces if f.verts[0][pidl] == 2]; 
dark_b = dark_uv(bpy.path.abspath('//../textures/skel_basecolor_final.png'), fb, uvb); dark_h = (0.0005, 0.0005)
print('DARK', dark_b, dark_h)
faces = [f for f in bm.faces if f.verts[0][pidl] in LIN]
geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
d = bmesh.ops.duplicate(bm, geom=geom)
nf = [g for g in d['geom'] if isinstance(g, bmesh.types.BMFace)]
bmesh.ops.reverse_faces(bm, faces=nf)
for f in nf:
    for l in f.loops:
        l[uvb].uv = dark_b; l[uvh].uv = dark_h
print('LINING faces', len(nf))
for f in nf: f[lin] = 1
dfm = bm.verts.layers.deform.active
if 'Bone01' not in body.vertex_groups: body.vertex_groups.new(name='Bone01')
names = [g.name for g in body.vertex_groups]
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# --- dagger: pommel -> tip along the knuckle line (MM9's handle), blade plane from MM9's
Z = np.load(bpy.path.abspath('//dagger_mesh.npz')); dag = np.load(bpy.path.abspath('//dagger_rest.npz'))
V, F, UV, PX = Z['v'], Z['f'], Z['uv'], float(Z['px_m'])
d_ = unit(AX)
nb = unit(dag['normal'] - d_ * (dag['normal'] @ d_))
U = np.cross(nb, d_)
GRIP_PX = np.array([300.0, 521.0])                         # the fist's middle on the grip in the master
u = (V[:, 0] - GRIP_PX[0]) * PX; v = -(V[:, 1] - GRIP_PX[1]) * PX; z = V[:, 2] * PX
off = ((mcp - G) @ d_) * d_
Pw = G + off[None] + np.outer(u, d_) + np.outer(v, U) + np.outer(z, nb)
print('SCIMITAR tip', np.round(Pw[np.argmax(V[:, 0])], 3), 'pommel', np.round(Pw[np.argmin(V[:, 0])], 3), 'MM9 tip', np.round(dag['verts'][np.argmin(dag['verts'][:, 1])], 3))
new = [bm.verts.new(tuple(p)) for p in Pw]
bm.verts.index_update(); bm.verts.ensure_lookup_table()
bone = names.index('Bone01')
sf = []
for t_, sd in zip(F, Z['side']):
    f = bm.faces.new([new[int(i)] for i in t_])
    f[scl] = 1; sf.append(f)
    f.normal_update()
    c_f = np.array(tuple(f.calc_center_median())) - (G + off); ax_ = c_f - d_ * (c_f @ d_)     # outward from the dagger's axis
    if abs(np.array(tuple(f.normal)) @ d_) < 0.9 and np.array(tuple(f.normal)) @ ax_ < 0: f.normal_flip()
idx = {v: i for i, v in enumerate(new)}
for f in sf:
    for l in f.loops:
        l[uvb].uv = tuple(UV[idx[l.vert]]); l[uvh].uv = tuple(UV[idx[l.vert]])
for v in new:
    v[dfm][bone] = 1.0; v[pidl] = 400
bm.to_mesh(me); bm.free(); me.update()
# Bone01 at the grip
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones['Bone01']; IW = np.linalg.inv(W)
pt = (IW @ np.r_[G + off, 1])[:3]; dl = Vector(pt) - eb.head; eb.head += dl; eb.tail += dl
bpy.ops.object.mode_set(mode='OBJECT')
# --- joints closed: Meshy left air between some pieces (detached audit: fingers 4-6 mm, ankle and knee 9-11 mm in a pose). Each subtree moves along its parent bone toward the joint; verts follow rigidly
me.update()
TIGHT = [('Thumb1', 0.006), ('Middle3', 0.008), ('Hand', 0.004), ('Foot', 0.009), ('Calf', 0.007), ('Forearm', 0.007)]
rest_w = lambda n_: np.array(rig.data.bones[n_].head_local)
bpy.ops.object.mode_set(mode='OBJECT')
for s_ in 'RL':
    for bn, dist in TIGHT:
        root = rig.data.bones[f'Bip01 {s_} {bn}']
        sub = [root.name] + [c.name for c in root.children_recursive]
        par = root.parent
        dv = unit(np.array(par.head_local) - np.array(root.head_local)) * dist
        gi = {g.index for g in body.vertex_groups if g.name in sub}
        vs = [v for v in me.vertices if v.groups and max(v.groups, key=lambda g: g.weight).group in gi]
        for v in vs: v.co += Vector(dv)
        bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='EDIT')
        for n_ in sub:
            eb = rig.data.edit_bones[n_]; eb.head += Vector(dv); eb.tail += Vector(dv)
        bpy.ops.object.mode_set(mode='OBJECT')
        print('SPIKES tighten', root.name, len(vs), 'verts')
me.update()
print('FACES', len(me.polygons), 'verts', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
