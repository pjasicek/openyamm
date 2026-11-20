"""Mouth for the sheep: open the lips, add a cavity and give the lower jaw to Xjawpiv (hinged at the mouth corners).

MM9 opens the jaw (Xjawpiv) by up to 3.7 cm at the chin in die2, 2 cm in fidget1 (grazing) and 1.5 cm in walk. The
Meshy head is one closed shell with a lip crease, and its nearest-MM9 labels put Xjawpiv on the throat, so:
1. The muzzle faces in front of the mouth corners are bisected along the mouth plane (through the front lip crease,
   rising slightly to the corners) and the cut edges are split: a slit from corner to corner round the front. The
   corners stay joined (the hinge).
2. A cavity is built behind the slit: rings from the lip edges inward and back toward the throat, the upper half
   rising into a palate, the lower half sinking into a floor with a tongue ridge (each ring vertex at least 3 mm
   inside the outer skin), closed by a small throat cap. Upper rings follow Xhead, lower rings Xjawpiv, the corner
   and the cap blend both. Face attribute 'cavity' = 1 marks it for compose (mouth paint) and the UVs.
3. Jaw weights: below the mouth line and in front of the jaw angle the skin follows Xjawpiv (a sharp split at the
   slit, a soft blend behind the corners); the old Xjawpiv weight elsewhere (the throat) moves to Xheadpiv.
Args: <in blend> <out blend> <report json>
"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
FRONT = np.array([0.0, -0.700, 0.779])     # lip crease at the front (bind)
SLOPE = 0.09                                # mouth line rises 0.09 per metre toward the corners
Y_CORNER = -0.652                           # mouth corners
Y_JAW_FULL, Y_JAW_END = -0.60, -0.552       # the jaw follows fully in front of -0.60, fades out at the jaw angle
DEPTH_Y = -0.628                            # cavity back end (throat cap)
RINGS = 5


def line_z(y):
    return FRONT[2] + SLOPE * (y - FRONT[1])


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']
me = o.data
groups = {g.name: g.index for g in o.vertex_groups}
JAW, HEAD, HEADPIV = groups['Xjawpiv'], groups['Xhead'], groups['Xheadpiv']
bm = bmesh.new(); bm.from_mesh(me)
dl = bm.verts.layers.deform.active
bvh_outer = BVHTree.FromBMesh(bm)
piece_l = bm.verts.layers.int.get('piece')

# ---- 1. slit
n = Vector((0, -SLOPE, 1)).normalized()
co = Vector(tuple(FRONT))
region = [f for f in bm.faces if all(v.co.y < Y_CORNER + 0.004 and 0.74 < v.co.z < 0.82 and abs(v.co.x) < 0.06
                                     for v in f.verts) and (piece_l is None or f.verts[0][piece_l] == 0)]
geom = list(set([e for f in region for e in f.edges] + [v for f in region for v in f.verts] + region))
import os
MODE = os.environ.get('MODE', 'all')    # cut: slit + jaw weights (dense mesh); cavity: cavity on the existing slit
cut = []
if MODE in ('all', 'cut'):
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=n, dist=0.0002)
    cut = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    cut = [e for e in cut if max(v.co.y for v in e.verts) < Y_CORNER and len(e.link_faces) == 2]
    bmesh.ops.split_edges(bm, edges=cut)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
bnd = [e for e in bm.edges if len(e.link_faces) == 1 and min(v.co.y for v in e.verts) < Y_CORNER + 0.002]
loop_v = list({v for e in bnd for v in e.verts})


def side(v):
    c = sum((f.calc_center_median() for f in v.link_faces), Vector()) / max(1, len(v.link_faces))
    return 1 if c.z - line_z(c.y) > 0 else -1


upper = [v for v in loop_v if side(v) > 0]
lower = [v for v in loop_v if side(v) < 0]


def order(vs):
    # along the lip from the right corner (-x) round the front to the left corner (+x): sort by the angle about a
    # point behind the mouth
    c = Vector((0, Y_CORNER + 0.03, FRONT[2]))
    return sorted(vs, key=lambda v: math.atan2(v.co.x - c.x, -(v.co.y - c.y)))


upper, lower = order(upper), order(lower)
sgn_of = {}
for v in loop_v:
    ups = sum(1 for e in v.link_edges if len(e.link_faces) == 1 and side(e.other_vert(v)) > 0)
    los = sum(1 for e in v.link_edges if len(e.link_faces) == 1 and side(e.other_vert(v)) < 0)
    sgn_of[v] = side(v) if not (v.co.y > Y_CORNER - 0.006) else 0   # the corner vertices: no bulge, 50/50

# ---- 2. cavity: extrude the lip loop inward RINGS times (extrusion keeps the winding consistent), then close it
cap_c = Vector((0.0, DEPTH_Y, line_z(DEPTH_Y) + 0.002))


def ring_pos(p0, k, sgn):
    """Ring k of the cavity behind lip point p0: ring 1 rolls the lip inward (a 4 mm lip), the next rings run back to
    the throat cap, the upper half rising into the palate, the lower sinking into the floor (tongue ridge)."""
    f = (k - 1) / (RINGS - 1) if RINGS > 1 else 1.0
    if k == 1:
        hit = bvh_outer.find_nearest(p0)
        nrm = hit[1] if hit[0] is not None else Vector((0, -1, 0))
        p = p0 - nrm * 0.004 + Vector((0, 0.002, 0.002 * sgn))
    else:
        x = p0.x * (1 - 0.55 * f)
        y = p0.y + 0.006 + (cap_c.y - p0.y - 0.006) * f
        bulge = math.sin(math.pi * min(1.0, f * 1.1)) * (0.008 if sgn > 0 else 0.005 if sgn < 0 else 0.0)
        tongue = (0.003 * math.cos(min(1.0, abs(x) / 0.015) * math.pi / 2) if sgn < 0 else 0.0) * f
        z = p0.z + 0.003 * sgn + (cap_c.z - p0.z) * f + sgn * bulge + tongue
        p = Vector((x, y, z))
    hit = bvh_outer.find_nearest(p)
    if hit[0] is not None:
        loc, nrm, _, dist = hit
        if (p - loc).dot(nrm) > -0.003:
            p = loc - nrm * 0.003
    return p


def weight(v, w_jaw):
    for gi in list(v[dl].keys()):
        del v[dl][gi]
    if w_jaw > 0:
        v[dl][JAW] = w_jaw
    if w_jaw < 1:
        v[dl][HEAD] = 1 - w_jaw


cav_verts, new_faces = [], []
if MODE in ('all', 'cavity'):
    orig_faces = {tuple(sorted(v.index for v in f.verts)) for f in bm.faces}
    bm.verts.index_update()
    edges = bnd
    origin = {v: (v.co.copy(), sgn_of[v]) for v in loop_v}
    for k in range(1, RINGS + 1):
        ret = bmesh.ops.extrude_edge_only(bm, edges=edges)
        nv = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMVert)]
        ne = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMEdge)]
        nf = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMFace)]
        new_faces += nf
        # each new vertex was duplicated from an old one at the same place: inherit its lip origin
        new_origin = {}
        for v in nv:
            src = next(e.other_vert(v) for e in v.link_edges if e.other_vert(v) in origin)
            new_origin[v] = origin[src]
        for v, (p0, sg) in new_origin.items():
            v.co = ring_pos(p0, k, sg)
            weight(v, 0.5 if sg == 0 or k == RINGS else (0.0 if sg > 0 else 1.0))
            cav_verts.append(v)
        origin = new_origin
        edges = [e for e in ne if all(v in new_origin for v in e.verts)]
    # close the throat: collapse the last ring to its centre
    last = list(origin)
    cc = sum((v.co for v in last), Vector()) / len(last)
    bmesh.ops.pointmerge(bm, verts=last, merge_co=cc)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    bm.verts.index_update()
    new_faces = [f for f in bm.faces if tuple(sorted(v.index for v in f.verts)) not in orig_faces]
    cav_verts = [v for v in cav_verts if v.is_valid]
cav_attr = bm.faces.layers.int.get('cavity') or bm.faces.layers.int.new('cavity')
for f in bm.faces:
    f[cav_attr] = 0
for f in new_faces:
    if f.is_valid:
        f[cav_attr] = 1
chain_l = bm.verts.layers.int.get('chain')
for v in cav_verts:
    if piece_l is not None:
        v[piece_l] = 0
    if chain_l is not None:
        v[chain_l] = -1

# ---- 3. jaw weights on the outer skin
cav_set = set(cav_verts)
lip_set = set(loop_v)
moved = 0
if MODE in ('all', 'cut'):
    for v in bm.verts:
        if v in cav_set or (piece_l is not None and v[piece_l] != 0):
            continue
        y, z = v.co.y, v.co.z
        s = z - line_z(min(y, Y_CORNER + 0.03))
        if y < Y_CORNER:
            below = smooth(0.002, -0.002, s)
        else:
            below = smooth(0.010, -0.014, s)
        fy = smooth(Y_JAW_END, Y_JAW_FULL, y)
        wj = float(below * fy)
        d = v[dl]
        old = {g: w for g, w in d.items()}
        oj = old.pop(JAW, 0.0)
        if oj > 0:
            old[HEADPIV] = old.get(HEADPIV, 0.0) + oj
            moved += 1
        tot = sum(old.values()) or 1.0
        for gi in list(d.keys()):
            del d[gi]
        for g, w in old.items():
            if w * (1 - wj) / tot > 1e-3:
                d[g] = w * (1 - wj) / tot
        if wj > 1e-3:
            d[JAW] = wj
# limit to four influences, normalised
for v in bm.verts:
    d = v[dl]
    items = sorted(d.items(), key=lambda t: -t[1])[:4]
    tot = sum(w for _, w in items) or 1.0
    for gi in list(d.keys()):
        del d[gi]
    for g, w in items:
        d[g] = w / tot
print('CAVITY_BM', sum(1 for f in bm.faces if f[cav_attr] == 1))
if MODE != 'cut':
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
print('CAVITY_BM2', sum(1 for f in bm.faces if f[cav_attr] == 1))
bm.normal_update()
bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
jaw_verts = sum(1 for v in me.vertices if any(g.group == JAW and g.weight > 0.5 for g in v.groups))
rep = {'slit_edges': len(cut), 'lip_upper': len(upper), 'lip_lower': len(lower), 'cavity_verts': len(cav_verts),
       'cavity_faces': sum(1 for p in me.polygons if me.attributes['cavity'].data[p.index].value == 1),
       'jaw_verts': jaw_verts, 'throat_jaw_weight_moved': moved, 'verts': len(me.vertices), 'tris': len(me.polygons)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('MOUTH ' + json.dumps(rep))
