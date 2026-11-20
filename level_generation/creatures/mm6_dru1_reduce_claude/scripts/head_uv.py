"""New head-set UV layout on work/head_parts.blend (Cand_66, face attribute 'hpart': 1 face skin, 2 hair, 3 hood):
layer 'HeadUV' in 0..1 for the head faces, face attribute 'uvpart'.
- Face front: a geodesic disc around the nose tip (R_FACE, default 0.10 m) of the face part, angle-based unwrap as one
  island at full density (one island over the whole head left the face a small dense patch in the middle of a
  conformal map dominated by scalp and neck).
- Face rest (scalp under the hair, ears, neck): seam down the back midline, angle-based, lower density.
- Hood: a closed shell; outer surface and lining (faces turned toward the head) unwrap as one sheet each,
  angle-based (a Smart UV Project split it into thin strips). Hair shell: Smart UV Project at A_HAIR degrees.
Islands are normalised to their 3D area, scaled by DENSITY per uvpart (face 1.4, scalp/neck/ears 0.35, hair 0.6, hood 0.18: about the body cloak's 2.9 texels/cm), then packed by an own shelf packer
(skyline, both orientations; bpy.ops.uv.pack_islands needs a UV editor and does nothing in background mode).
-> work/head_uv.blend; prints texels/cm per part for a 1024 head set."""
import os, math, heapq, bpy, bmesh
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = lambda k, d: float(os.environ.get(k, d))
# uvpart: 1 face front, 4 face rest, 2 hair, 3 hood outer, 5 hood lining
DENSITY = {1: E('D_FACE', '1.4'), 4: E('D_REST', '.35'), 2: E('D_HAIR', '.6'), 3: E('D_HOOD', '.18'), 5: E('D_HOOD', '.18')}
NAMES = {1: 'face', 4: 'scalp/neck/ears', 2: 'hair', 3: 'hood outer', 5: 'hood lining'}
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'head_parts.blend'))
c = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_66')]; me = c.data
for o in bpy.data.objects:
    o.hide_set(o != c); o.select_set(o == c)
bpy.context.view_layer.objects.active = c
hp = np.zeros(len(me.polygons), np.int32); me.attributes['hpart'].data.foreach_get('value', hp)
if 'HeadUV' in me.uv_layers: me.uv_layers.remove(me.uv_layers['HeadUV'])
me.uv_layers.new(name='HeadUV'); me.uv_layers.active = me.uv_layers['HeadUV']
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
for e in bm.edges: e.seam = False


def dijkstra(src, allowed_edge, cost=lambda e, w: e.calc_length()):
    dist = {src: 0.0}; prev = {}; pq = [(0.0, src.index, src)]
    while pq:
        d, _, v = heapq.heappop(pq)
        if d > dist[v]: continue
        for e in v.link_edges:
            if not allowed_edge(e): continue
            w = e.other_vert(v); nd = d + cost(e, w)
            if nd < dist.get(w, 1e9): dist[w] = nd; prev[w] = (v, e); heapq.heappush(pq, (nd, w.index, w))
    return dist, prev


def seam_path(prev, start, goal):
    v = goal; n = 0
    while v is not start:
        v, e = prev[v]; e.seam = True; n += 1
    return n


def part_edge(part):
    return lambda e: any(hp[f.index] == part for f in e.link_faces)


# face front disc around the nose tip
fv = {v for f in bm.faces if hp[f.index] == 1 for v in f.verts}
zs = np.array([v.co.z for v in fv])
nose = min((v for v in fv if 1.50 < v.co.z < 1.60), key=lambda v: v.co.y)
dist, _ = dijkstra(nose, part_edge(1))
R = E('R_FACE', '.10')
up = np.zeros(len(me.polygons), np.int32)
for f in bm.faces:
    if hp[f.index] == 1:
        up[f.index] = 1 if all(dist.get(v, 1e9) < R for v in f.verts) else 4
    elif hp[f.index] > 1:
        up[f.index] = hp[f.index]
# the disc may leave tiny enclaves (nostrils, mouth corners) outside: faces of the rest enclosed by the disc join it
for _ in range(3):
    for f in bm.faces:
        if up[f.index] == 4:
            nb = [g for e in f.edges for g in e.link_faces if g is not f]
            if nb and all(up[g.index] == 1 for g in nb):
                up[f.index] = 1
cy = np.mean([v.co.y for v in fv])
# rest of the face part: back seam from the lowest back boundary vertex to the crown
rest_v = {v for f in bm.faces if up[f.index] == 4 for v in f.verts}
seen, comps = set(), []
for f in bm.faces:
    if up[f.index] != 4 or f.index in seen: continue
    st, comp = [f], []; seen.add(f.index)
    while st:
        g = st.pop(); comp.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if up[h.index] == 4 and h.index not in seen: seen.add(h.index); st.append(h)
    comps.append(comp)
main = {v for f in max(comps, key=len) for v in f.verts}
bnd = [v for v in main if any(up[f.index] not in (4,) for f in v.link_faces) and v.co.y > cy]
start = min(bnd, key=lambda v: v.co.z - 4 * v.co.y + 6 * abs(v.co.x)); goal = max(main, key=lambda v: v.co.z)
_, prev = dijkstra(start, lambda e: all(w in main for w in e.verts) and part_edge(1)(e),
                   lambda e, w: e.calc_length() * (1 + 40 * abs(w.co.x) + (8 if w.co.y < cy else 0)))
print('SEAM rest', seam_path(prev, start, goal))
# hood: a closed shell (outer surface and lining meet at the rim, no open edge): lining = faces turned toward the
# head (uvpart 5), the rim between them is the seam; each side unwraps as one sheet
head_c = Vector(np.mean([v.co[:] for v in fv], axis=0))
nl = 0
for f in bm.faces:
    if up[f.index] == 3 and f.normal.dot(head_c - f.calc_center_median()) > 0:
        up[f.index] = 5; nl += 1
print('HOOD lining faces', nl, 'outer', int((up == 3).sum()))
for e in bm.edges:
    if len({up[f.index] for f in e.link_faces}) > 1: e.seam = True
bm.to_mesh(me); bm.free()
a = me.attributes.get('uvpart') or me.attributes.new('uvpart', 'INT', 'FACE'); a.data.foreach_set('value', up.tolist())


def select(parts):
    bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons: p.select = bool(up[p.index] in parts)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE')


select({1, 4, 3, 5}); bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, margin=0.0)
select({2}); bpy.ops.uv.smart_project(angle_limit=math.radians(E('A_HAIR', '80')), island_margin=0.0, scale_to_bounds=False)
select({1, 2, 3, 4, 5}); bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale()
bpy.ops.object.mode_set(mode='OBJECT')
uv = me.uv_layers['HeadUV'].data
for p in me.polygons:
    if up[p.index] > 0:
        for l in p.loop_indices: uv[l].uv = uv[l].uv * DENSITY[int(up[p.index])]
# islands by shared UV edges
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); ul = bm.loops.layers.uv['HeadUV']
isl = {}; islands = []
for f in bm.faces:
    if up[f.index] == 0 or f.index in isl: continue
    st = [f]; isl[f.index] = len(islands); cur = [f.index]
    while st:
        g = st.pop(); gl = {x.vert: x[ul].uv for x in g.loops}
        for lp in g.loops:
            e = lp.edge
            for h in e.link_faces:
                if h is g or up[h.index] == 0 or h.index in isl: continue
                hl = {x.vert: x[ul].uv for x in h.loops}
                if all((hl[v] - gl[v]).length < 1e-6 for v in e.verts):
                    isl[h.index] = len(islands); cur.append(h.index); st.append(h)
    islands.append(cur)
bm.free()
loops = [[l for fi in i_ for l in me.polygons[fi].loop_indices] for i_ in islands]
boxes = []
for ls in loops:
    P = np.array([uv[l].uv[:] for l in ls]); best = None
    for ang in np.linspace(0, np.pi / 2, 46):
        Rm = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]]); Q = P @ Rm.T; wh = Q.max(0) - Q.min(0)
        if best is None or wh[0] * wh[1] < best[0]: best = (wh[0] * wh[1], ang, Q.min(0), wh)
    if best[3][0] < best[3][1]:  # lay islands flat (wide shelves pack tighter)
        ang = best[1] + np.pi / 2; Rm = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]]); Q = P @ Rm.T
        best = (best[0], ang, Q.min(0), Q.max(0) - Q.min(0))
    boxes.append(best)
GAP = E('MARGIN', '.006')


def skyline(scale):
    """bottom-left skyline packing in the unit square, each island tried in both orientations; tallest first"""
    order = sorted(range(len(boxes)), key=lambda i: -max(boxes[i][3]) * min(boxes[i][3]))
    sky = [(0.0, 1.0, GAP)]  # segments (x, width, height)
    pos = {}
    for i in order:
        w0, h0 = boxes[i][3] * scale + GAP
        best = None
        for rot, (w, h) in ((False, (w0, h0)), (True, (h0, w0))):
            for j, (x, _, _) in enumerate(sky):
                if x + w > 1 - GAP + 1e-9: break
                # height over [x, x + w)
                top = 0; k = j; xe = x
                while xe < x + w - 1e-12 and k < len(sky):
                    top = max(top, sky[k][2]); xe = sky[k][0] + sky[k][1]; k += 1
                if top + h > 1 + 1e-9: continue
                if best is None or (top + h, x) < (best[0], best[1]): best = (top + h, x, top, w, h, rot)
        if best is None: return False, pos
        _, x, top, w, h, rot = best
        pos[i] = (x + GAP / 2, top + GAP / 2, rot)
        # raise the skyline over [x, x + w)
        new = []
        for (sx, sw, sh) in sky:
            ex = sx + sw
            if ex <= x or sx >= x + w: new.append((sx, sw, sh)); continue
            if sx < x: new.append((sx, x - sx, sh))
            if ex > x + w: new.append((x + w, ex - x - w, sh))
        new.append((x, w, top + h)); new.sort()
        merged = []
        for seg in new:
            if merged and abs(merged[-1][2] - seg[2]) < 1e-12 and abs(merged[-1][0] + merged[-1][1] - seg[0]) < 1e-12:
                merged[-1] = (merged[-1][0], merged[-1][1] + seg[1], seg[2])
            else: merged.append(seg)
        sky = merged
    return True, pos


lo_s, hi_s = 1e-3, 1e3
for _ in range(60):
    mid = (lo_s * hi_s) ** .5
    if skyline(mid)[0]: lo_s = mid
    else: hi_s = mid
_, pos = skyline(lo_s)
for i, ls in enumerate(loops):
    _, ang, mn, wh = boxes[i]; Rm = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
    x, y, rot = pos[i]
    for l in ls:
        q = (np.array(uv[l].uv[:]) @ Rm.T - mn) * lo_s
        if rot: q = np.array([wh[1] * lo_s - q[1], q[0]])
        uv[l].uv = Vector(q + (x, y))
print('PACKED', len(islands), 'islands')


def tri_area(t): return abs((t[1][0] - t[0][0]) * (t[2][1] - t[0][1]) - (t[2][0] - t[0][0]) * (t[1][1] - t[0][1])) / 2


tot = 0
for part in (1, 4, 2, 3, 5):
    ua = sum(tri_area([uv[l].uv for l in p.loop_indices]) for p in me.polygons if up[p.index] == part)
    a3 = sum(p.area for p in me.polygons if up[p.index] == part); tot += ua
    print('DENSITY %-16s %4d faces, uv %.3f, %.1f texels/cm at 1024' % (NAMES[part], int((up == part).sum()), ua, 1024 * math.sqrt(ua / a3) / 100))
print('COVERAGE %.3f' % tot)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'head_uv.blend'))
