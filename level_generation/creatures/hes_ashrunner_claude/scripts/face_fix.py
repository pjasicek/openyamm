"""Face polish (2026-10-22 review) on the textured master, in place: the hood's front lip off the left eye and welding
goggles over the hood from the concept (fam_ashrunners.png: two round brass-rimmed dark lenses on the forehead, the
strap round the hood). Idempotent (mesh custom property 'face_fix'); run after sync_actions.py (build_runtime.sh).
1. Hood lip (P03, Smart Topology folded its front edge diagonally across the left eye): hood vertices in front of the
   face (rest y < FRONT_Y) inside the eye window (an ellipse in x/z round the eyes, above the scarf: weight ramps in
   from SCARF_Z) are moved radially out of the window in x/z to its edge (+ MARGIN); the displacement is diffused over
   the hood's edges (DIFFUSE passes, pinned movers) so the cloth folds back smoothly. Vertices move; none is deleted.
2. Goggles (new piece GOGGLE_PIECE, garment 3, 100 % B_Head, head-protected in the LOD0 halving): two lens cups
   (12-gon, brass rim wall and lip, dark lens inset) placed by ray-cast on the hood above the brow, tilted up the
   forehead, a nose bridge, and a strap ray-cast round the hood 4 mm off its surface to the back of the head. Texture:
   rim and bridge on the body set's brass (UVMap, BRASS_PX, metal class), the strap on its dark leather, the lenses on
   the head set's dark goggle lens (HeadUV, LENS_PX, glazed class); one texel each, outside every region, so the tiers
   never recolour them. Smart Topology's own goggles (the P10 ring half buried under the brim, the P25/P81 buckle bits
   poking out of the hood's back) are replaced by these (their vertices removed).
Args: -- <blend> [out blend (default: in place)]"""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
src = os.path.abspath(a[0]); out = os.path.abspath(a[1]) if len(a) > 1 else src
E = os.environ.get
FRONT_Y, SCARF_Z, MARGIN, DIFFUSE = float(E('FRONT_Y', '-0.175')), float(E('SCARF_Z', '1.605')), 1.08, int(E('DIFFUSE', '20'))
WIN = dict(cx=float(E('WIN_CX', '-0.010')), cz=float(E('WIN_CZ', '1.650')), ax=float(E('WIN_AX', '0.062')),
           az=float(E('WIN_AZ', '0.047')))   # eyes x -0.048..0.029, z 1.638..1.665; the brim keeps the forehead
GZ, GSEP = float(E('GOGGLE_Z', '1.738')), float(E('GOGGLE_SEP', '0.037'))
R_OUT, R_IN, R_LENS, DEPTH, SEG = 0.021, 0.0155, 0.0165, 0.015, 12
# one texel each: textures/har_basecolor_1k.png brass (184, 136, 77) and dark leather (78, 53, 35), har_head_basecolor_1k.png
# goggle lens (35, 28, 25); found as the most uniform patches of those classes (compose_har.py PREVIEW class maps)
BRASS_PX, LEATHER_PX, LENS_PX, N = (776, 900), (414, 462), (28, 47), 1024
HOOD, OLD_GOGGLES, GOGGLE_PIECE = 3, (10, 25, 81), 103
bpy.ops.wm.open_mainfile(filepath=src)
body = bpy.data.objects['Body']; me = body.data
if me.get('face_fix'):
    print('FACEFIX already applied', src)
    sys.exit(0)
assert not me.shape_keys, 'shape keys are not handled'
assert (body.matrix_world - Matrix.Identity(4)).to_3x3().to_quaternion().angle < 1e-6
print('FACEFIX attributes', [(x.name, x.domain, x.data_type) for x in me.attributes if not x.name.startswith('.')])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
pl = bm.verts.layers.int['piece']; gl = bm.verts.layers.int.get('garment')
ol = bm.verts.layers.float_vector.get('orig_co')
hl = bm.faces.layers.int['head']
dl = bm.verts.layers.deform.verify()
uvb, uvh = bm.loops.layers.uv['UVMap'], bm.loops.layers.uv['HeadUV']
HEADG = body.vertex_groups['B_Head'].index
# ------------------------------------------------------------------ 1. hood lip out of the eye window
hood = [v for v in bm.verts if v[pl] == HOOD]
D = {}
for v in hood:
    x, y, z = v.co
    if y > FRONT_Y:
        continue
    dx, dz = (x - WIN['cx']) / WIN['ax'], (z - WIN['cz']) / WIN['az']; r = math.hypot(dx, dz)
    wz = min(1.0, max(0.0, (z - SCARF_Z) / 0.025)); wz = wz * wz * (3 - 2 * wz)
    if r >= MARGIN or wz <= 0:
        continue
    if r < 1e-6:
        dx, dz, r = 0.0, 1.0, 1e-6
    k = (MARGIN - r) / r * wz
    D[v] = Vector((dx * k * WIN['ax'], 0.0, dz * k * WIN['az']))
movers = set(D)
near = [v for v in hood if v not in movers and min(((v.co - m.co).length for m in movers), default=1) < 0.06]
for v in near:
    D[v] = Vector()
for _ in range(DIFFUSE):
    new = {}
    for v in near:
        nb = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) in D]
        if nb:
            new[v] = sum((D[u] for u in nb), Vector()) / len(nb)
    D.update(new)
for v, d in D.items():
    v.co += d
print('FACEFIX hood lip moved', len(movers), 'diffused', len(near), 'max cm',
      round(100 * max((d.length for d in D.values()), default=0), 2))
# ------------------------------------------------------------------ remove Smart Topology's goggle ring
ring = [v for v in bm.verts if v[pl] in OLD_GOGGLES]
bmesh.ops.delete(bm, geom=ring, context='VERTS')
print('FACEFIX old goggle ring and strap-buckle vertices removed', len(ring))
# ------------------------------------------------------------------ 2. goggles on the hood
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
hood_faces = [f for f in bm.faces if all(v[pl] == HOOD for v in f.verts)]
tree = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in hood_faces])


def cast(origin, direction):
    loc, n, i, d = tree.ray_cast(origin, direction)
    if loc is None:
        return None, None
    if n.dot(direction) > 0:
        n = -n
    return loc, n.normalized()


cx = WIN['cx']
assert all(cast(Vector((cx + s * GSEP, -0.6, GZ)), Vector((0, 1, 0)))[0] for s in (-1, 1)), 'no hood under the goggles'
hits = [cast(Vector((cx + s * GSEP, -0.6, GZ)), Vector((0, 1, 0))) for s in (-1, 1)]
print('FACEFIX goggle hits on the hood', [tuple(round(x, 3) for x in h[0]) for h in hits])
axis = Vector((0, -1, float(E('GOGGLE_TILT', '0.5')))).normalized()   # pushed up the forehead: they look ~27 deg up
side = Vector((1, 0, 0)); up = axis.cross(side).normalized(); side = up.cross(axis).normalized()
new_v, new_f = [], []


def V(p):
    v = bm.verts.new(p); v[pl] = GOGGLE_PIECE
    if ol is not None:
        v[ol] = p
    if gl is not None:
        v[gl] = 3
    v[dl].clear(); v[dl][HEADG] = 1.0
    new_v.append(v); return v


def F(vs, lens=False, tex='brass'):
    f = bm.faces.new(vs); f[hl] = 1 if lens else 0; f.smooth = True; new_f.append((f, 'lens' if lens else tex)); return f


def ring_pts(c, r):
    return [c + (side * math.cos(t) + up * math.sin(t)) * r for t in (2 * math.pi * k / SEG for k in range(SEG))]


cups = []
for loc, n in hits:
    c0 = loc - axis * 0.011; c1 = loc + axis * DEPTH; cl = loc + axis * (DEPTH - 0.004)
    back = [V(p) for p in ring_pts(c0, R_OUT * 1.03)]
    wall = [V(p) for p in ring_pts(c1, R_OUT)]
    lip_o = [V(p) for p in ring_pts(c1, R_OUT)]; lip_i = [V(p) for p in ring_pts(c1, R_IN)]
    inner = [V(p) for p in ring_pts(c1, R_IN)]; inner_b = [V(p) for p in ring_pts(cl, R_IN)]
    lens = [V(p) for p in ring_pts(cl, R_LENS)]; lc = V(cl - axis * 0.0015)
    for k in range(SEG):
        j = (k + 1) % SEG
        F([back[k], back[j], wall[j], wall[k]])                          # outer wall (outward)
        F([lip_o[k], lip_o[j], lip_i[j], lip_i[k]])                      # front lip
        F([inner[k], inner[j], inner_b[j], inner_b[k]])                  # inner wall down to the glass
        F([lens[k], lens[j], lc], lens=True)                             # glass, slightly domed in
    cups.append((loc, c1))
# nose bridge: a 4 x 6 mm bar between the cups' inner rims
p0 = cups[0][1] + side * R_OUT * 0.9 - axis * 0.006; p1 = cups[1][1] - side * R_OUT * 0.9 - axis * 0.006
hb, hd = up * 0.003, axis * 0.004
bv = [V(p) for p in (p0 - hb, p0 + hb, p0 + hb + hd, p0 - hb + hd, p1 - hb, p1 + hb, p1 + hb + hd, p1 - hb + hd)]
bc = (p0 + p1) / 2 + hd / 2
for q in ((0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
    f = F([bv[i] for i in q]); f.normal_update()
    if f.normal.dot(f.calc_center_median() - bc) < 0:
        f.normal_flip()
# strap: from each cup's outer rim round the hood to the back of the head
band = [v.co for v in hood if abs(v.co.z - GZ) < 0.02]
hc = Vector((float(np.mean([p.x for p in band])), float(np.mean([p.y for p in band])), GZ))
nstrap = 0
for s, (loc, c1) in zip((-1, 1), cups):
    start = loc + side * s * R_OUT * 0.95
    t0 = math.atan2(s * (start.x - hc.x), -(start.y - hc.y))
    prev = None
    for k in range(12):
        t = t0 + (math.pi - t0) * k / 11
        zz = GZ - 0.03 * (k / 11) ** 2                                    # a little lower round the back
        d = Vector((s * math.sin(t), -math.cos(t), 0)).normalized()
        o = Vector((hc.x, hc.y, zz))
        q, n = cast(o + d * 0.4, -d)
        if q is None:                                                   # past the hood's edge: the strap ends there
            break
        p = q + n * 0.004
        u = (Vector((0, 0, 1)) - n * n.z).normalized() * 0.008
        pair = (V(p - u), V(p + u))
        if prev:
            f = F([prev[0], pair[0], pair[1], prev[1]], tex='leather'); f.normal_update()
            if f.normal.dot(n) < 0:
                f.normal_flip()
            nstrap += 1
        prev = pair
# texture: one texel each (brass on the body set, the dark lens on the head set)
UVS = {k: Vector(((p[0] + 0.5) / N, 1 - (p[1] + 0.5) / N)) for k, p in (('brass', BRASS_PX), ('leather', LEATHER_PX), ('lens', LENS_PX))}
for f, tex in new_f:
    f.normal_update()
    for lo in f.loops:
        lo[uvb].uv = UVS[tex]; lo[uvh].uv = UVS[tex]
bm.to_mesh(me); bm.free(); me.update()
me['face_fix'] = 1
print('FACEFIX goggles', len(new_v), 'vertices', len(new_f), 'faces; strap quads', nstrap,
      'lens centres', [tuple(round(x, 3) for x in l) for l, _ in cups], 'axis', tuple(round(x, 2) for x in axis))
bpy.ops.wm.save_as_mainfile(filepath=out)
