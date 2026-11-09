"""UV atlas for the unrigged cleric mesh (work/step1_v1.blend -> work/step1_uv.blend), adapted from
mm6_thf_claude/scripts/uv_thf.py. Regions: face, hair, belt tongue; torso front/back and tunic skirt front/back;
sleeve and hand per side; leg per side (front/back) and boot per side; the collar; the mantle outer/inner; the cloak
by sector (back, his left, his right) and surface (outer, inner). Hidden faces (torso under the mantle, legs under the
skirt, the cloak's inner back) share one low-density region. Sleeves unwrap with an extra seam on their hidden side;
hands and boots use sharp-edge seams, the belt and hidden faces Smart UV Project. Folded triangles are cut out and the
unwrap repeated until the 1024^2 overlap raster is clean."""
import bpy, bmesh, sys, os, math, json, collections
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
mesh = bpy.data.objects['Cleric']; me = mesh.data
PARTS = json.loads(bpy.context.scene['cle_parts'])
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')

SHOULDER = {1: Vector((0.19, -0.05, 1.25)), -1: Vector((-0.19, -0.05, 1.25))}
WRIST = {1: Vector((0.30, -0.07, 0.85)), -1: Vector((-0.30, -0.07, 0.85))}
COLLAR_Z, MANTLE_Z, BELT_Z, BOOT_Z = 1.30, 1.13, 0.93, 0.40
METHOD = os.environ.get('UV_METHOD', 'MINIMUM_STRETCH')
SIDE = {1: 'L', -1: 'R'}                                   # character left = +X
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
hidv = np.zeros(len(me.vertices)); me.attributes['hid'].data.foreach_get('value', hidv)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()


def region(f):
    p = PARTS[part[f.index]]; c = f.calc_center_median(); sx = 1 if c.x > 0 else -1
    hidden = all(hidv[v.index] > 0.5 for v in f.verts)
    if p in ('Head', 'Hair', 'Belt'):
        return p
    if p == 'Torso':
        if c.z < WRIST[sx].z - 0.005 and c.x * sx > 0.235:
            return 'Hand' + SIDE[sx]
        s, w = SHOULDER[sx], WRIST[sx]; d = (w - s).normalized(); t = (c - s).dot(d)
        if t > 0 and (c - s - d * t).length < 0.085 and c.x * sx > 0.15:
            return 'Arm' + SIDE[sx]
        if hidden:
            return 'Hidden'
        if c.z < BELT_Z:
            return 'Skirt' + ('F' if c.y < -0.03 else 'B')
        return 'TorsoF' if c.y < -0.03 else 'TorsoB'
    if p == 'Legs':
        if c.z < BOOT_Z:
            return 'Boot' + SIDE[sx]
        if hidden:
            return 'Hidden'
        return 'Leg' + SIDE[sx] + ('F' if c.y < -0.06 else 'B')
    if p == 'Cloak':
        if c.z > COLLAR_Z:
            return 'Collar'
        radial = Vector((c.x, c.y + 0.03, 0)).normalized()
        inner = f.normal.dot(radial) < 0
        if c.z > MANTLE_Z:
            return 'Mantle' + ('i' if inner else '')
        if inner and hidden:
            return 'Hidden'
        a = math.degrees(math.atan2(c.x, c.y))                # 0 = back, +90 = his left
        sec = 'B' if abs(a) < 55 else ('L' if a > 0 else 'R')
        return 'Cloak' + sec + ('i' if inner else '')
    return p


freg = [region(f) for f in bm.faces]
for _ in range(3):                                        # majority filter on region speckle (same part only)
    nxt = list(freg)
    for f in bm.faces:
        nb = [freg[g.index] for e in f.edges for g in e.link_faces if g is not f and part[g.index] == part[f.index]]
        if nb:
            top = max(set(nb), key=nb.count)
            if nb.count(top) * 2 > len(nb):
                nxt[f.index] = top
    freg = nxt
bm.free()
print('REGIONS', dict(collections.Counter(freg)))
SMART = {'Hidden': 66, 'Belt': 66}
# armour shells, hands and feet: seams on sharp edges (plate rims, finger sides), then the same unwrap as the tubes;
# Smart UV Project gave 886 islands (183 on the skirt), mostly slivers under 4 faces
SHARP = {r: 60 for r in ('HandL', 'HandR', 'BootL', 'BootR')}
SMALL = set(SMART)


def axis_frame(region):
    """(origin, axis, hidden-side direction) for the extra seam in tube-like regions."""
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
BIAS = {'Head': 1.8, 'HandR': 1.3, 'HandL': 1.3, 'Collar': 1.1, 'Mantle': 1.1, 'Mantlei': 0.6, 'CloakBi': 0.6,
        'CloakLi': 0.7, 'CloakRi': 0.7, 'BootL': 0.9, 'BootR': 0.9, 'Belt': 1.2, 'Hidden': 0.35}
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
bpy.context.scene['cle_uv_regions'] = json.dumps(names)
print('UV regions', names, 'seams', sum(1 for e in me.edges if e.use_seam))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_uv.blend'))
