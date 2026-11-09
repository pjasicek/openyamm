"""Chest repair of the reduced Swordsman (work/ladder_facecape.blend, Cand_62 -> work/ladder_chest.blend), matching
the native sprite and the HD masters:
- the Meshy 'chain link' bits (studs along the capelet hem, necklace bits floating in front of the tunic) are removed;
- the capelet hem gets a twisted cord: overlapping, alternately tilted lumps along the hem path the studs traced
  (work/beads.npy), sitting on the capelet surface, weighted like the capelet under them;
- a gold necklace hangs in a V from the clasp ends to a hexagonal pendant with a gem, lying on the tunic, weighted
  like the tunic under it (the pendant rigidly);
- the clasp is made symmetric: its left end knob (the clean rolled end) and the left half of its bar are mirrored
  over the bar's centre.
Rig, clips and every other vertex are untouched. Usage: blender -b -P chest_repair.py"""
import math, os, bmesh, bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORD_STEP, CORD = .016, (.0125, .0062, .0045)      # spacing; half length, width, thickness of a cord lump (m)
LINK_STEP, LINK = .0095, (.0068, .0030, .0014)     # necklace link spacing and half sizes
PENDANT_Z, PENDANT_R = 1.248, .0125
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_facecape.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
cand = bpy.data.objects['Cand_62']; me = cand.data; mw = cand.matrix_world; inv = mw.inverted()
groups = {g.index: g.name for g in cand.vertex_groups}
weights = [[(g.group, g.weight) for g in v.groups] for v in me.vertices]

# face classes from the installed region mask (red: cloak and capelet)
mask = bpy.data.images.load(os.path.join(HERE, 'work', 'region_mask.png'))
W, H = mask.size; px = np.array(mask.pixels[:], np.float32).reshape(H, W, 4)
uvd = me.uv_layers.active.data
cloak_face = []
for p in me.polygons:
    u = np.mean([uvd[li].uv[0] for li in p.loop_indices]); v = np.mean([uvd[li].uv[1] for li in p.loop_indices])
    cloak_face.append(px[min(int(v * H), H - 1), min(int(u * W), W - 1), 0] > .5)

bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
deform = bm.verts.layers.deform.verify(); uvl = bm.loops.layers.uv.active
part_layer = bm.faces.layers.int.new('chest_part')  # 1 cord, 2 necklace link, 3 pendant plate, 4 gem


def pieces():
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop(); comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index); stack.append(y)
        out.append(comp)
    return out


world = lambda v: mw @ v.co
comps = pieces()
centre = lambda c: sum((world(v) for v in c), Vector()) / len(c)
beads = [c for c in comps if len(c) <= 6 and 1.15 < centre(c).z < 1.45]
ends = sorted((c for c in comps if 20 <= len(c) <= 40 and centre(c).y < -.12 and 1.35 < centre(c).z < 1.40
               and abs(centre(c).x) > .03),
              key=lambda c: centre(c).x)
bar = [c for c in comps if 35 <= len(c) <= 60 and centre(c).y < -.12 and 1.36 < centre(c).z < 1.41 and abs(centre(c).x) < .03]
assert len(ends) == 2 and len(bar) == 1, (len(ends), len(bar))
left, right = ends
clasp_ids = {v.index for c in ends + bar for v in c}; bead_ids = {v.index for c in beads for v in c}
cx = (centre(left).x + centre(right).x) / 2
print('REMOVE beads', len(beads), 'clasp ends at x', round(centre(left).x, 4), round(centre(right).x, 4), 'mirror x', round(cx, 4))

# clasp: mirror the left knob over x = cx, replacing the right one
dup = bmesh.ops.duplicate(bm, geom=list({f for v in left for f in v.link_faces}) + left)
newv = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMVert)]
for v in newv:
    p = world(v); v.co = inv @ Vector((2 * cx - p.x, p.y, p.z))
    flipped = {}
    for gi, wgt in v[deform].items():
        n = groups[gi]; m = n.replace('_L_', '_X_').replace('_R_', '_L_').replace('_X_', '_R_')
        flipped[cand.vertex_groups[m].index if m in cand.vertex_groups else gi] = wgt
    v[deform].clear()
    for gi, wgt in flipped.items():
        v[deform][gi] = wgt
bmesh.ops.reverse_faces(bm, faces=[g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)])
# the bar: its left half mirrored onto the right (bmesh symmetrize about x = cx, in world space)
barv = bar[0]; barf = list({f for v in barv for f in v.link_faces}); barE = list({e for v in barv for e in v.link_edges})
for v in barv:
    v.co = world(v) - Vector((cx, 0, 0))
sym = bmesh.ops.symmetrize(bm, input=barv + barE + barf, direction='-X', dist=1e-5)
symv = [g for g in sym['geom'] if isinstance(g, bmesh.types.BMVert)]
for v in symv:
    v.co = inv @ (v.co + Vector((cx, 0, 0)))
    if v.co.x != v.co.x:
        raise ValueError('nan')
for v in symv:  # mirrored vertices take their left twin's weights (the bar is on the spine)
    if not v[deform].items():
        twin = min((u for u in symv if u[deform].items()), key=lambda u: ((mw @ u.co) - Vector((2 * cx - (mw @ v.co).x, (mw @ v.co).y, (mw @ v.co).z))).length)
        for gi, wgt in twin[deform].items():
            v[deform][gi] = wgt
print('BAR verts', len(barv), '->', len(symv))
bmesh.ops.delete(bm, geom=right + [v for c in beads for v in c], context='VERTS')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()

# surfaces to sit on (original faces only), world space
orig = me.polygons
cv = [mw @ v.co for v in me.vertices]
def surface(sel):
    idx = [p.index for p in orig if sel(p)]
    return BVHTree.FromPolygons(cv, [orig[i].vertices[:] for i in idx]), idx
cloak_bvh, cloak_idx = surface(lambda p: cloak_face[p.index])
tunic_bvh, tunic_idx = surface(lambda p: not cloak_face[p.index] and not (set(p.vertices) & (clasp_ids | bead_ids)))


def nearest_weights(bvh, idx, p):
    loc, n, fi, d = bvh.find_nearest(p)
    poly = orig[idx[fi]]
    vi = min(poly.vertices, key=lambda i: (cv[i] - loc).length)
    return loc, n, weights[vi], poly


def add_vert(p, wts, uv_from):
    v = bm.verts.new(inv @ p)
    for gi, wgt in wts:
        v[deform][gi] = wgt
    return v


def add_faces(tris, poly, part):
    uv = uvd[poly.loop_indices[0]].uv.copy()
    for t, prt in zip(tris, part if isinstance(part, list) else [part] * len(tris)):
        f = bm.faces.new(t); f.material_index = 0; f.smooth = True; f[part_layer] = prt
        for loop in f.loops:
            loop[uvl].uv = uv


def octa(c, t, b, n, size, wts, poly, part, bvh=None, idx=None):
    """elongated octahedron (8 triangles) on frame t (length), b (width), n (thickness); weights per vertex from the
    surface below it when a surface is given, otherwise all `wts` (rigid)"""
    L, Wd, T = size; pts = {('t', 1): c + t * L, ('t', -1): c - t * L, ('b', 1): c + b * Wd, ('b', -1): c - b * Wd,
                             ('n', 1): c + n * T, ('n', -1): c - n * T}
    vs = {}
    for key, p in pts.items():
        vs[key] = add_vert(p, nearest_weights(bvh, idx, p)[2] if bvh else wts, None)
    tris = []
    for st in (1, -1):
        for sb in (1, -1):
            for sn in (1, -1):
                tri = [vs[('t', st)], vs[('b', sb)], vs[('n', sn)]]
                tris.append(tri if st * sb * sn > 0 else tri[::-1])
    add_faces(tris, poly, part)
    return len(tris)


def resample(points, step, closed):
    pts = np.array(points)
    if closed:
        pts = np.vstack([pts, pts[:1]])
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
    n = max(int(round(s[-1] / step)), 2); q = np.linspace(0, s[-1], n, endpoint=not closed)
    return np.stack([np.interp(q, s, pts[:, k]) for k in range(3)], 1)


# cord along the capelet hem
bd = np.load(os.path.join(HERE, 'work', 'beads.npy'))
neck = (bd[:, 1] < -.12) & (np.abs(bd[:, 0] - cx) < .065) & (bd[:, 2] < 1.35)
hem = bd[~neck]; mid = hem.mean(0)
hem = hem[np.argsort(np.arctan2(hem[:, 1] - mid[1], hem[:, 0] - mid[0]))]
path = resample(hem, .004, True)
for _ in range(3):  # circular smoothing (about 4 cm)
    path = sum(np.roll(path, k, 0) for k in range(-5, 6)) / 11
path = resample(path, CORD_STEP, True)
tris = 0
for i, p in enumerate(path):
    loc, n, wts, poly = nearest_weights(cloak_bvh, cloak_idx, Vector(p))
    t = Vector(path[(i + 1) % len(path)] - path[i - 1]).normalized()
    n = (n - t * n.dot(t)).normalized(); b = n.cross(t)
    a = math.radians(32 if i % 2 else -32)          # alternate tilt: a twisted, braided read
    t2 = t * math.cos(a) + b * math.sin(a); b2 = n.cross(t2)
    tris += octa(loc + n * (CORD[2] * .6), t2, b2, n, CORD, None, poly, 1, cloak_bvh, cloak_idx)
print('CORD lumps', len(path), 'tris', tris, 'length m', round(len(path) * CORD_STEP, 2))

# necklace: two link chains from the clasp ends' lower edge to the pendant, lying on the tunic
pend = Vector((cx, -.15, PENDANT_Z)); ploc, pn, pw, ppoly = nearest_weights(tunic_bvh, tunic_idx, pend)
ntris = 0
for side in (-1, 1):
    end = left if side < 0 else None
    start = Vector((cx + side * .047, -.15, 1.356))
    top = ploc + Vector((0, 0, PENDANT_R * .95))
    raw = [start.lerp(top, k / 40) + Vector((0, 0, -.012 * math.sin(math.pi * k / 40))) for k in range(41)]
    raw = [nearest_weights(tunic_bvh, tunic_idx, p)[0] for p in raw]
    pts = resample([p[:] for p in raw], LINK_STEP, False)
    for i, p in enumerate(pts):
        loc, n, wts, poly = nearest_weights(tunic_bvh, tunic_idx, Vector(p))
        t = Vector(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = (n - t * n.dot(t)).normalized(); b = n.cross(t)
        if i % 2:   # alternate links stand edge-on
            b, n = n, -b
        ntris += octa(loc + (n if i % 2 == 0 else b) * .003, t, b, n, LINK, wts, poly, 2)
# pendant: gold hexagonal plate with a raised gem, rigid on the tunic below it
nrm = pn.normalized(); up = (Vector((0, 0, 1)) - nrm * nrm.z).normalized(); rt = up.cross(nrm)
c0 = ploc + nrm * .0045
ring = lambda r, d: [add_vert(c0 + nrm * d + (rt * math.cos(math.radians(60 * k + 30)) + up * math.sin(math.radians(60 * k + 30))) * r, pw, None) for k in range(6)]
front, back = ring(PENDANT_R, .0022), ring(PENDANT_R, -.0022)
fc, bc = add_vert(c0 + nrm * .0022, pw, None), add_vert(c0 - nrm * .0022, pw, None)
gem = ring(PENDANT_R * .58, .0026); apex = add_vert(c0 + nrm * .0068, pw, None)
pt = []
for k in range(6):
    j = (k + 1) % 6
    pt += [[fc, front[k], front[j]], [bc, back[j], back[k]], [front[k], back[k], back[j]], [front[k], back[j], front[j]],
           [apex, gem[k], gem[j]]]
pt = [[a, b, c] if ((b.co - a.co).cross(c.co - a.co)).dot(inv.to_3x3() @ nrm) >= 0 or i % 5 == 2 or i % 5 == 3 else [a, c, b]
      for i, (a, b, c) in enumerate(pt)]
add_faces(pt, ppoly, [4 if i % 5 == 4 else 3 for i in range(len(pt))]); ntris += len(pt)
print('NECKLACE links+pendant tris', ntris)

bm.normal_update()
bm.to_mesh(me); bm.free(); me.update()
print('TOTAL tris', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_chest.blend'))
