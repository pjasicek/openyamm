"""UV atlas for the unrigged titan mesh (work/step1_v1.blend -> work/step1_uv.blend), adapted from
mm6_gua_claude/scripts/uv_gua.py. Regions are geometric: torso (cuirass), head skin, upper/fore arm and hand per side
(the wrist at the bracer's lower rim), leg and foot per side (straight loop cut at the ankle band). Skin covered by
the pauldrons, bracers, bands, belt and helmet gets one low-density hidden region. Tubes (torso, arms, legs) unwrap
with an extra seam on their hidden side; hands, feet and every armour shell use Smart UV Project, which keeps each
skirt scale, plate and rim in one piece (ABF fragments armour shells into hundreds of islands, goblin lesson).
Folded triangles are cut out and the unwrap repeated until the 1024^2 overlap raster is clean."""
import bpy, bmesh, sys, os, math, json, collections
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
mesh = bpy.data.objects['Titan']; me = mesh.data
PARTS = json.loads(bpy.context.scene['ttn_parts'])
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')

SHOULDER = {1: Vector((0.22, 0.0, 1.20)), -1: Vector((-0.22, 0.0, 1.20))}
WRIST = {1: Vector((0.42, -0.05, 0.75)), -1: Vector((-0.42, -0.05, 0.75))}
ANKLE, HEAD_Z = 0.075, 1.29                             # ankle band bottom, chin/neck line (measured)
METHOD = os.environ.get('UV_METHOD', 'MINIMUM_STRETCH')
SIDE = {1: 'L', -1: 'R'}                                   # character left = +X


def body_region(p, name):
    sx = 1 if p.x > 0 else -1
    if name == 'Legs':
        return ('Foot' if p.z < ANKLE else 'Leg') + SIDE[sx]
    if p.z > HEAD_Z:
        return 'Head'
    s, w = SHOULDER[sx], WRIST[sx]
    d = (w - s).normalized(); L = (w - s).length
    t = (p - s).dot(d)
    if t > L - 0.005 and abs(p.x) > 0.30:
        return 'Hand' + SIDE[sx]
    if t > 0 and (p - s - d * t).length < 0.11 and p.x * sx > 0.20:
        return 'Arm' + SIDE[sx]
    return 'Torso'


# straight edge loop at the ankle, so the foot/leg texture border is a clean seam
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
pl = bm.faces.layers.int.get('part')
legs = PARTS.index('Legs')
geom = [f for f in bm.faces if f[pl] == legs and 0.03 < f.calc_center_median().z < 0.12]
geom = geom + list({e for f in geom for e in f.edges}) + list({v for f in geom for v in f.verts})
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Vector((0, 0, ANKLE)), plane_no=Vector((0, 0, 1)))
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(me); bm.free()
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
COVERS = {'Body': ('Pauldron', 'Bracer', 'Band', 'Belt', 'Helmet', 'Dome', 'Nape'), 'Legs': ('Greave', 'Knee', 'Belt')}
trees = {}
for inner, outer in COVERS.items():
    fs = [f for f in bm.faces if PARTS[part[f.index]] in outer]
    vi = sorted({v.index for f in fs for v in f.verts}); remap = {v: i for i, v in enumerate(vi)}
    trees[inner] = BVHTree.FromPolygons([bm.verts[v].co.copy() for v in vi], [[remap[v.index] for v in f.verts] for f in fs])


def covered(f):
    """Face centre and every corner are under a covering shell along the normal (within 4 cm)."""
    t = trees.get(PARTS[part[f.index]])
    if t is None:
        return False
    pts = [(f.calc_center_median(), f.normal)] + [(v.co, v.normal) for v in f.verts]
    return all(t.ray_cast(p + n * 1e-4, n, 0.04)[0] is not None for p, n in pts)


BODY = ('Body', 'Legs')
breg = {f.index: body_region(f.calc_center_median(), PARTS[part[f.index]]) for f in bm.faces
        if PARTS[part[f.index]] in BODY}
# Meshy fused the left greave into the leg shell: its faces lie on the mirrored right greave (x -> -x)
gf = [f for f in bm.faces if PARTS[part[f.index]] == 'Greave']
gv = sorted({v.index for f in gf for v in f.verts}); gr = {v: i for i, v in enumerate(gv)}
mirror = BVHTree.FromPolygons([Vector((-bm.verts[v].co.x, bm.verts[v].co.y, bm.verts[v].co.z)) for v in gv],
                              [[gr[v.index] for v in f.verts] for f in gf])
fused = set()
for f in bm.faces:
    c = f.calc_center_median()
    if PARTS[part[f.index]] == 'Legs' and c.x > 0 and 0.08 < c.z < 0.38:
        hit = mirror.find_nearest(c)
        if hit[0] is not None and hit[3] < 0.012 and f.normal.dot(Vector((-hit[1].x, hit[1].y, hit[1].z))) > 0.3:
            breg[f.index] = 'GreaveFused'; fused.add(f.index)
print('FUSED_GREAVE faces', len(fused))
# front/back halves of the torso and legs (side seams through the armpits / along the legs): flat disks pack well
for f in bm.faces:
    r = breg.get(f.index, '')
    if r == 'Torso' or r.startswith('Leg'):
        c = f.calc_center_median()
        breg[f.index] = r + ('F' if c.y < (0.0 if r == 'Torso' else 0.01) else 'B')
CUT = {'Foot', 'Leg', 'GreaveFused'}                                   # the ankle border runs on the new loop and stays
for _ in range(3):
    nxt = dict(breg)
    for f in bm.faces:
        if f.index not in breg:
            continue
        nb = [breg[g.index] for e in f.edges for g in e.link_faces if g is not f and g.index in breg]
        top = max(set(nb), key=nb.count) if nb else breg[f.index]
        pair = {breg[f.index].rstrip('LRFB'), top.rstrip('LRFB')}
        if nb.count(top) * 2 > len(nb) and not pair <= CUT:
            nxt[f.index] = top
    breg = nxt

fv = sorted({v.index for i in fused for v in bm.faces[i].verts}); fr = {v: i for i, v in enumerate(fv)}
fused_tree = BVHTree.FromPolygons([bm.verts[v].co.copy() for v in fv], [[fr[v.index] for v in bm.faces[i].verts]
                                                                       for i in fused])
cov = [covered(f) or (f.index not in fused and PARTS[part[f.index]] == 'Legs' and all(
    fused_tree.ray_cast(p + n * 1e-4, n, 0.04)[0] is not None
    for p, n in [(f.calc_center_median(), f.normal)] + [(v.co, v.normal) for v in f.verts])) for f in bm.faces]
for _ in range(3):                                      # majority filter: contiguous hidden patches, no speckle
    nxt = list(cov)
    for f in bm.faces:
        nb = [g for e in f.edges for g in e.link_faces if g is not f and part[g.index] == part[f.index]]
        if nb:
            k = sum(cov[g.index] for g in nb)
            nxt[f.index] = k * 2 > len(nb) or (k * 2 == len(nb) and cov[f.index])
    cov = nxt


def face_region(f):
    p = PARTS[part[f.index]]
    if p not in BODY:
        return p
    r = breg[f.index]
    if cov[f.index] and not r.startswith(('Hand', 'Foot', 'Head', 'Greave')):
        return 'Hidden'
    return r


freg = [face_region(f) for f in bm.faces]
bm.free()
SMART = {'Hidden': 66, 'Nape': 66}
# armour shells, hands and feet: seams on sharp edges (plate rims, finger sides), then the same unwrap as the tubes;
# Smart UV Project gave 886 islands (183 on the skirt), mostly slivers under 4 faces
SHARP = {r: 60 for r in ('Skirt', 'Belt', 'Pauldron', 'Bracer', 'Band', 'Greave', 'GreaveFused', 'Knee', 'Helmet',
                         'Dome', 'Crest', 'HandL', 'HandR', 'FootL', 'FootR')}
SMALL = set(SMART)


def axis_frame(region):
    """(origin, axis, hidden-side direction) for the extra seam in tube-like regions."""
    if region == 'Head':
        return Vector((0, 0.05, 0)), Vector((0, 0, 1)), Vector((0, 1, 0))       # back
    for sx, sd in SIDE.items():
        if region == 'Arm' + sd:
            d = (WRIST[sx] - SHOULDER[sx]).normalized()
            return SHOULDER[sx], d, Vector((-sx, 0, -0.3))                     # inner side
    return None


bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
for e in bm.edges:
    e.seam = len(e.link_faces) == 2 and freg[e.link_faces[0].index] != freg[e.link_faces[1].index]
for e in bm.edges:
    if len(e.link_faces) == 2 and freg[e.link_faces[0].index] == freg[e.link_faces[1].index] in SHARP:
        if e.calc_face_angle(0.0) > math.radians(SHARP[freg[e.link_faces[0].index]]):
            e.seam = True
for region in set(freg) - SMALL:
    frame = axis_frame(region)
    if frame is None:
        continue
    origin, axis, ref = frame
    ref = (ref - axis * ref.dot(axis)).normalized(); side_ref = axis.cross(ref).normalized()
    faces = [f for f in bm.faces if freg[f.index] == region]; fset = {f.index for f in faces}
    ang = {}
    for f in faces:
        for v in f.verts:
            d = v.co - origin; d -= axis * d.dot(axis)
            ang[v.index] = math.atan2(d.dot(side_ref), d.dot(ref))             # 0 = hidden side
    for f in faces:
        for e in f.edges:
            a, b = (ang[v.index] for v in e.verts)
            if abs(a) < math.pi / 2 and abs(b) < math.pi / 2 and a * b <= 0 and all(lf.index in fset for lf in e.link_faces):
                e.seam = True
bmesh.update_edit_mesh(me)
bpy.ops.object.mode_set(mode='OBJECT')
edge_lookup = {e.key: e.index for e in me.edges}
BIAS = {'Head': 1.8, 'HandR': 1.3, 'HandL': 1.3, 'Helmet': 1.2, 'Dome': 1.1, 'Crest': 0.9, 'Belt': 1.2,
        'FootL': 0.9, 'FootR': 0.9, 'Hidden': 0.35, 'Nape': 0.4}
for attempt in range(8):
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select = freg[f.index] not in SMALL
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.unwrap(method=METHOD, margin=0.0)
    for angle in sorted(set(SMART.values())):
        bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
        for f in bm.faces:
            f.select = SMART.get(freg[f.index]) == angle
        bmesh.update_edit_mesh(me)
        bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=0.0, scale_to_bounds=False)
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active

    def uv_area(f):
        pts = [l[uv].uv for l in f.loops]
        return abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y
                       for i in range(len(pts)))) / 2

    # collapsed or badly stretched unwraps (fingers folded onto the palm, leg backs): Smart UV Project instead
    dens = collections.defaultdict(list)
    for f in bm.faces:
        if f.calc_area() > 1e-9:
            dens[freg[f.index]].append(math.sqrt(uv_area(f) / f.calc_area()))
    redo = [r for r, d in dens.items() if r not in SMALL and (np.percentile(d, 10) < 0.5 * np.median(d)
                                                             or np.percentile(d, 90) > 3 * np.percentile(d, 10))]
    if redo:
        print('SMART_FALLBACK', attempt, sorted(redo))
        for f in bm.faces:
            f.select = freg[f.index] in redo
        bmesh.update_edit_mesh(me)
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, scale_to_bounds=False)
        bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active

    def uv_area(f):
        pts = [l[uv].uv for l in f.loops]
        return abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y
                       for i in range(len(pts)))) / 2

    # every UV island to its region's density (per island, so a stray single-triangle island cannot stay huge)
    key = lambda l: (round(l[uv].uv.x, 6), round(l[uv].uv.y, 6))
    island = {}
    for f in bm.faces:
        if f.index in island:
            continue
        island[f.index] = f.index; st = [f]
        while st:
            g = st.pop()
            for l in g.loops:
                for h in l.edge.link_faces:
                    if h.index in island or h is g:
                        continue
                    lh = next(x for x in h.loops if x.edge == l.edge)
                    if {key(l), key(l.link_loop_next)} == {key(lh), key(lh.link_loop_next)}:
                        island[h.index] = f.index; st.append(h)
    by_island = collections.defaultdict(list)
    for f in bm.faces:
        by_island[island[f.index]].append(f)
    for faces in by_island.values():
        a3 = sum(f.calc_area() for f in faces); a2 = sum(uv_area(f) for f in faces)
        if a2 <= 0 or a3 <= 0:
            continue
        k = math.sqrt(a3 / a2) * BIAS.get(freg[faces[0].index], 1.0)
        loops = [l for f in faces for l in f.loops]
        c = sum((l[uv].uv for l in loops), Vector((0, 0))) / len(loops)
        for l in loops:
            l[uv].uv = c + (l[uv].uv - c) * k
    for f in bm.faces:
        f.select = True
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode='OBJECT')
    me.calc_loop_triangles(); uvl = me.uv_layers.active.data; R = 1024
    owner = np.full((R, R), -1, dtype=np.int64); overlap = set()
    for ti, t in enumerate(me.loop_triangles):
        p = np.array([tuple(uvl[li].uv) for li in t.loops]) * R
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, R - 1), min(y1, R - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a_, b_, c_ = p
        d = (b_[1] - c_[1]) * (a_[0] - c_[0]) + (c_[0] - b_[0]) * (a_[1] - c_[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b_[1] - c_[1]) * (gx - c_[0]) + (c_[0] - b_[0]) * (gy - c_[1])) / d
        w1 = ((c_[1] - a_[1]) * (gx - c_[0]) + (a_[0] - c_[0]) * (gy - c_[1])) / d
        inside = (w0 > 0.02) & (w1 > 0.02) & (1 - w0 - w1 > 0.02)
        ys, xs = np.nonzero(inside)
        prev = owner[y0 + ys, x0 + xs]
        if (prev >= 0).any():
            overlap.add(ti); overlap.update(int(q) for q in np.unique(prev[prev >= 0]))
        owner[y0 + ys, x0 + xs] = ti
    where = collections.Counter(freg[me.loop_triangles[ti].polygon_index] for ti in overlap)
    print('ATTEMPT', attempt, 'OVERLAP_TRIS', len(overlap), dict(where))
    if not overlap:
        break
    for pi in {me.loop_triangles[ti].polygon_index for ti in overlap}:
        for ek in me.polygons[pi].edge_keys:
            me.edges[edge_lookup[ek]].use_seam = True
reg_attr = me.attributes.new('uv_region', 'INT', 'FACE')
names = sorted(set(freg)); reg_attr.data.foreach_set('value', [names.index(r) for r in freg])
bpy.context.scene['ttn_uv_regions'] = json.dumps(names)
print('UV regions', names, 'seams', sum(1 for e in me.edges if e.use_seam))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_uv.blend'))
