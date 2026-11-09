"""After the paint (UVs frozen), geometry that shares existing texels, on the rigged master:
- lining: open plates (skirt, belt, helmet shell and guards, pauldrons) are single-sided, so a view of their inside showed the
  background (Yrsa's sleeves). Each gets a coincident inner copy, flipped, same weights, on one dark texel of its own set.
- hips: Meshy has no pelvis, the femurs ended in the air under the skirt: the top of each femur is copied, on its own texels, as
  a bar from the hip joint to the spine base, rigid on Bip01 Spine.
- scimitar (work/scimitar_mesh.npz): rigid on Bone01, moved to the handle axis in the fist, faces with attribute `scim`. The
  handle lies along MM9's handle direction, the blade in MM9's blade plane, and the knuckle line is on that handle (fit_skelwar).
- fist: the fingers are solved round the handle cylinder per finger on a grid, the thumb over them. Poses are bone-local
  rotations in work/hand_poses.json, keyed by finger_keys.py: grip (R), relaxed and throw (L).
Args: <in blend> <out blend> <hand poses json>"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
IN, OUT, POSES = sys.argv[sys.argv.index('--') + 1:]
MID = -0.0037
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
ch = lambda s, f: np.array([H(f'Bip01 {s} {f}{i}') for i in (1, 2, 3)] + [T(f'Bip01 {s} {f}3')])


def rot(ax, a):
    return np.array(Matrix.Rotation(a, 3, Vector(ax)))


# --- grip
J = {f: ch('R', f) for f in FINGERS + ('Thumb',)}
kn = unit(J['Index'][0] - J['Pinky'][0])
f0 = unit(np.mean([J[f][1] - J[f][0] for f in FINGERS], 0)); f0 = unit(f0 - kn * (f0 @ kn))
n0 = np.cross(kn, f0)
if (np.mean([J[f][3] for f in FINGERS], 0) - np.mean([J[f][0] for f in FINGERS], 0)) @ n0 < 0:
    print('palm normal flipped'); n0 = -n0
R_GRIP, FR = 0.0175, 0.0095
mcp = np.mean([J[f][0] for f in FINGERS], 0)
G = mcp + f0 * 0.022 + n0 * (R_GRIP + FR + 0.003)
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
            p1 = t[0] + R2 @ (t[1] - t[0]); p2 = p1 + R3 @ (t[2] - t[1]); p3 = p2 + R3 @ (t[3] - t[2])
            s = samples(np.array([t[0], p1, p2, p3])); r = radial(s)
            c = np.linalg.norm(p3 - target) + 3 * np.maximum(R_GRIP + 0.007 - r, 0).sum()
            if best is None or c < best[0]: best = (c, (R2, R3), (th, ph, ps), p3)
print('THUMB', np.round(np.degrees(best[2]), 0), 'tip to target', round(np.linalg.norm(best[3] - target), 3))
grip.update(chain_pose('R', 'Thumb', [best[1][0], best[1][1], best[1][1]]))
# left hand: mirror axes
JL = {f: ch('L', f) for f in FINGERS + ('Thumb',)}
S = np.diag([-1.0, 1, 1])
axL = S @ AX
sL = -sg


def curl(s, ax, sign, a, thumb):
    res = {}
    for f in FINGERS:
        res.update(chain_pose(s, f, [rot(ax, sign * a[0]), rot(ax, sign * (a[0] + a[1])), rot(ax, sign * (a[0] + a[1] + a[2]))]))
    res.update(chain_pose(s, 'Thumb', [rot(ax, sign * thumb[0]), rot(ax, sign * (thumb[0] + thumb[1])), rot(ax, sign * (thumb[0] + thumb[1] + thumb[1]))]))
    return res


relaxed = curl('L', axL, sL, np.radians((24, 30, 16)), np.radians((8, 10)))
throw = curl('L', axL, sL, np.radians((62, 72, 45)), np.radians((25, 25)))
json.dump(dict(grip=grip, relaxed=relaxed, throw=throw), open(POSES, 'w'), indent=0)

# --- lining + hips
bm = bmesh.new(); bm.from_mesh(me)
# eyes: the 32-triangle balls read as hexagons up close; one subdivision back onto the sphere (UVs and weights interpolate)
pl_ = bm.verts.layers.int['pid']
for ep in (19, 119):
    fs = [f for f in bm.faces if f.verts[0][pl_] == ep]
    vs = list({v for f in fs for v in f.verts}); c_ = sum((v.co for v in vs), Vector()) / len(vs)
    r_ = max((v.co - c_).length for v in vs)
    res = bmesh.ops.subdivide_edges(bm, edges=list({e for f in fs for e in f.edges}), cuts=1, use_grid_fill=True)
    for g in res['geom']:
        if isinstance(g, bmesh.types.BMFace):
            for v in g.verts: v[pl_] = ep
    all_v = list({v for f in bm.faces if f.verts[0][pl_] == ep for v in f.verts})
    for v in all_v: v.co = c_ + (v.co - c_).normalized() * r_
    tri = [f for f in bm.faces if f.verts[0][pl_] == ep and len(f.verts) > 3]
    if tri: bmesh.ops.triangulate(bm, faces=tri)
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
# spikes: the decimation left a few needle vertices on gauntlets and bones (a 4 cm thorn beside the pinky). The UVs stay; such a
# vertex goes back to the middle of its neighbours (armour edges and the skirt's points are real and not touched)
pl0 = bm.verts.layers.int['pid']
SMOOTH = {3, 6, 7, 10, 12, 23, 37, 0, 18}; SMOOTH |= {p + 100 for p in SMOOTH}
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
lin = bm.faces.layers.int.new('lining'); scl = bm.faces.layers.int.new('scim')
pidl = bm.verts.layers.int['pid']; uvb = bm.loops.layers.uv['UVMap']; uvh = bm.loops.layers.uv['HeadUV']
headl = bm.faces.layers.int['head']
LIN = [9, 14, 16, 25, 30, 32, 33, 38, 41, 42, 47, 49, 50, 56, 57, 58, 60, 61, 65, 21, 22, 26, 40, 54, 55, 63, 17, 35, 36, 59]
LIN = set(LIN) | {p + 100 for p in (26, 40, 54, 55, 63, 17, 35, 36, 59)}


def dark_uv(path, faces, layer):
    img = bpy.data.images.load(path, check_existing=True)
    h, w = img.size[1], img.size[0]; px = np.empty(h * w * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(h, w, 4)
    cs = []
    for f in faces:
        c = sum((np.array(tuple(l[layer].uv)) for l in f.loops), np.zeros(2)) / 3
        cs.append((px[min(h - 1, int(c[1] * h)), min(w - 1, int(c[0] * w)), :3] @ [.3, .6, .1], tuple(c)))
    cs.sort(key=lambda x: x[0])
    return cs[len(cs) // 12][1]


fb = [f for f in bm.faces if f.verts[0][pidl] == 8]; fh = [f for f in bm.faces if f.verts[0][pidl] == 21]
dark_b = dark_uv(bpy.path.abspath('//../textures/skelwar_basecolor_final.png'), fb, uvb)
dark_h = dark_uv(bpy.path.abspath('//../textures/skelwar_head_basecolor_final.png'), fh, uvh)
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
# hips: top of the femur (part 3 and its mirror) copied as a bar to the spine base
dfm = bm.verts.layers.deform.active
if 'Bone01' not in body.vertex_groups: body.vertex_groups.new(name='Bone01')
names = [g.name for g in body.vertex_groups]
spine_g = names.index('Bip01 Spine')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
sb = H('Bip01 Spine') + np.array([0, 0, -0.01]); 
for p, s in ((3, 'R'), (103, 'L')):
    fv = np.array([tuple(v.co) for v in bm.verts if v[pidl] == p and not any(l.face[lin] for l in v.link_loops)])
    hip = H(f'Bip01 {s} Thigh'); axis = unit(H(f'Bip01 {s} Calf') - hip)
    t_ = (fv - hip) @ axis
    faces = [f for f in bm.faces if f.verts[0][pidl] == p and all((np.array(tuple(v.co)) - hip) @ axis < 0.11 for v in f.verts)]
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    d = bmesh.ops.duplicate(bm, geom=geom)
    nv = [g for g in d['geom'] if isinstance(g, bmesh.types.BMVert)]
    Rm = np.array(Vector(axis).rotation_difference(Vector(unit(sb - hip))).to_matrix())
    L = np.linalg.norm(sb - hip) / 0.11 * 1.1
    for v in nv:
        q = np.array(tuple(v.co)) - hip
        along = (q @ axis) * axis
        v.co = Vector(hip + Rm @ (along * L + (q - along)))
        for k in list(v[dfm].keys()): del v[dfm][k]
        v[dfm][spine_g] = 1.0
        v[pidl] = 300
    print('HIP', s, len(nv), 'verts')
# --- skirt plates: rigid groups on small hinge bones at the belt (user review: thighs through the plates in walk and run)
GROUPS = {'front': [25, 57], 'front_R': [33], 'front_L': [41, 60], 'side_R': [30, 32, 16], 'side_L': [14, 49, 65],
          'back_R': [38, 50, 61], 'back_L': [42, 56, 58], 'back': [47]}
bones_new = {}
for g in GROUPS:
    n = f'Skirt_{g}'
    if n not in body.vertex_groups: body.vertex_groups.new(name=n)
names = [g.name for g in body.vertex_groups]
for g, ids in GROUPS.items():
    vs = [v for v in bm.verts if v[pidl] in ids]
    co_ = np.array([tuple(v.co) for v in vs])
    top = co_[co_[:, 2] > co_[:, 2].max() - 0.05].mean(0)
    n_ = co_.mean(0)[:2] - np.array([MID, 0.10]); n_ /= np.linalg.norm(n_)
    bones_new[g] = dict(pivot=top.tolist(), normal=[float(n_[0]), float(n_[1]), 0.0], pids=ids)
    gi = names.index(f'Skirt_{g}')
    for v in vs:
        for k in list(v[dfm].keys()): del v[dfm][k]
        v[dfm][gi] = 1.0
json.dump(bones_new, open(bpy.path.abspath('//skirt_groups.json'), 'w'), indent=1)
print('SKIRT groups', {g: len(b['pids']) for g, b in bones_new.items()})
# --- scimitar
Z = np.load(bpy.path.abspath('//scimitar_mesh.npz'))
V, F, UV, PX = Z['v'], Z['f'], Z['uv'], float(Z['px_m'])
hdir = unit(np.array([360 - 120.0, -(500 - 465.0)]))       # the grip in the master, image x right, y up
nb = unit(np.array([-0.8441584987880172, -0.4106186138330321, -0.34465748635101534]))
d_ = unit(AX - nb * (AX @ nb))
U = np.cross(nb, d_)
c_px = np.array([240.0, 483.0])
gpx = c_px
u = (V[:, 0] - gpx[0]) * PX; v = -(V[:, 1] - gpx[1]) * PX; z = V[:, 2] * PX
# align to G: move the grip centre (fingers sit toward the guard) so the knuckle centre is on the grip's middle
off = ((mcp - G) @ d_) * d_
Pw = G + off[None] + np.outer(u * hdir[0] + v * hdir[1], d_) + np.outer(-u * hdir[1] + v * hdir[0], U) + np.outer(z, nb)
print('SCIMITAR tip', np.round(Pw[np.argmax(V[:, 0])], 3), 'blade dir', np.round(unit(Pw[np.argmax(V[:, 0])] - G), 3), 'pommel', np.round(Pw[np.argmin(V[:, 0])], 3))
new = [bm.verts.new(tuple(p)) for p in Pw]
bm.verts.index_update(); bm.verts.ensure_lookup_table()
bone = names.index('Bone01')
sf = []
for t_, sd in zip(F, Z['side']):
    f = bm.faces.new([new[int(i)] for i in t_])
    f[scl] = 1; sf.append(f)
    f.normal_update()
    if np.array(tuple(f.normal)) @ nb * sd < 0: f.normal_flip()
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
for g, b_ in bones_new.items():
    eb = rig.data.edit_bones.new(f'Skirt_{g}')
    p_ = (IW @ np.r_[np.array(b_['pivot']), 1])[:3]
    eb.head = Vector(p_); eb.tail = Vector(p_) + Vector((0, 0, 0.1)); eb.parent = rig.data.edit_bones['Bip01 Spine']; eb.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
print('FACES', len(me.polygons), 'verts', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
