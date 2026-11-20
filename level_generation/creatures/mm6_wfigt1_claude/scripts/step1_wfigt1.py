"""Step 1 cleanup for the MM6 werewolf (Smart Topology v1 from references_hd/00_three_quarter.png).

Input work/st1_vis.blend (normalised 1.578 m, soles z=0, facing -Y; loose parts with per-face outside visibility from
analyse_parts.py). Parts (examine_parts.py, review/st1_parts_*.png): P00 body (torso, arms, clawed hands, neck, head),
P01 shorts fused with the right leg and a TAIL Meshy invented (no tail in the native sprites or the masters), P02 left
leg, P03/P04 feet, P05 pendant disc, P06 tongue, P07/P08 eye shells; ~128 closed beads form the necklace, ~27 closed
small parts in the mouth are teeth, open cards above z 1.25 are the mane and head fur, the rest are limb fur tufts.

- Tail: P01 vertices behind the buttock surface measured beside it (|x| 0.09-0.16, same height) by more than 1 cm,
  at |x| < 0.09, form the tail; its faces are deleted and the hole in the seat is filled and relaxed.
- Necklace: the beads (2.5k triangles) become one closed hexagonal tube through their centres (ordered by angle about
  the neck); the gold links come from the texture. Pendant disc kept (decimated).
- Eye shells deleted (the eyes are painted); teeth and tongue decimated; fur cards kept as they are.
- Region decimation (edit mode on selected faces): head (z > 1.26) and hands keep every vertex; hidden faces 0.3;
  torso/arms 0.6, shorts and legs 0.6, feet 0.5.
Joins everything into one mesh 'Werewolf' with a per-face 'part' attribute (index into scene['wfigt1_parts']).
Saves work/step1_v1.blend."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st1_vis.blend'))
O = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
info = {p['name']: p for p in json.load(open(os.path.join(common.WORK, 'st1_parts.json')))}
NAMED = {'P00': 'Body', 'P01': 'Shorts', 'P02': 'Leg', 'P03': 'Foot', 'P04': 'Foot', 'P05': 'Pendant',
         'P22': 'Pendant', 'P06': 'Tongue'}
DROP = {'P07', 'P08'}


def category(n):
    if n in NAMED:
        return NAMED[n]
    p = info[n]
    m = p['mean']
    ext = max(h - l for h, l in zip(p['hi'], p['lo']))
    if p['boundary'] == 0 and m[2] > 1.05 and m[1] > -0.26 and ext < 0.045 and p['tris'] >= 24:
        return 'Bead'           # 21 chain beads in a V across the chest (closed mane tufts are larger / coarser)
    if p['boundary'] == 0 and m[1] <= -0.26:
        return 'Teeth'
    return 'Mane' if m[2] > 1.25 else 'Fur'


groups = {}
hidden_cards = 0
for n, o in list(O.items()):
    m = info[n]['mean']
    if category(n) == 'Fur' and abs(m[0]) < 0.12 and m[1] > 0.2:          # tufts of the removed tail
        DROP.add(n)
    if category(n) in ('Mane', 'Fur') and not any(o['visible']):
        hidden_cards += 1
        DROP.add(n)
    if n in DROP:
        bpy.data.objects.remove(o, do_unlink=True)
        continue
    a = o.data.attributes.new('vis', 'INT', 'FACE')
    a.data.foreach_set('value', [int(x) for x in o['visible']])
    del o['visible']
    groups.setdefault(category(n), []).append(o)
before = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for g in groups.values() for o in g)

# necklace: bead centres -> tube
beads = groups.pop('Bead')
cent = np.array([np.mean([tuple(o.matrix_world @ v.co) for v in o.data.vertices], 0) for o in beads])
rad = float(np.median([np.ptp(np.array([tuple(v.co) for v in o.data.vertices]), 0).max() / 2 for o in beads]))
cx, cy = (cent[:, 0].min() + cent[:, 0].max()) / 2, float(cent[:, 1].max()) + 0.1
order = np.argsort(np.arctan2(cent[:, 0] - cx, cy - cent[:, 1]))     # front centre 0, his right < 0 < left
path = cent[order]
gaps = np.linalg.norm(path[1:] - path[:-1], axis=1)
print('NECKLACE beads', len(beads), 'radius', round(rad, 4), 'max gap', round(float(gaps.max()), 3))
for o in beads:
    bpy.data.objects.remove(o, do_unlink=True)
# open V over the chest; both ends continue 4 cm back round the neck (under the mane) along the end direction
ext0 = path[0] + (path[0] - path[2]) / np.linalg.norm(path[0] - path[2]) * 0.04
ext1 = path[-1] + (path[-1] - path[-3]) / np.linalg.norm(path[-1] - path[-3]) * 0.04
path = np.vstack([ext0, path, ext1])
for _ in range(2):
    path[1:-1] = (path[:-2] + 2 * path[1:-1] + path[2:]) / 4
s_ = np.concatenate([[0], np.cumsum(np.linalg.norm(path[1:] - path[:-1], axis=1))])
N, SIDES = 34, 6
pts = np.array([[np.interp(t, s_, path[:, k]) for k in range(3)] for t in np.linspace(0, s_[-1], N)])
bm = bmesh.new()
rings = []
u_prev = None
for i in range(N):
    p = Vector(pts[i])
    tng = Vector(pts[min(i + 1, N - 1)] - pts[max(i - 1, 0)]).normalized()
    u = (u_prev - tng * u_prev.dot(tng)).normalized() if u_prev is not None else tng.orthogonal().normalized()
    u_prev = u
    w = tng.cross(u)
    rings.append([bm.verts.new(p + (u * math.cos(2 * math.pi * k / SIDES) + w * math.sin(2 * math.pi * k / SIDES))
                               * rad * 0.85) for k in range(SIDES)])
for i in range(N - 1):
    r0, r1 = rings[i], rings[i + 1]
    for k in range(SIDES):
        bm.faces.new((r0[k], r0[(k + 1) % SIDES], r1[(k + 1) % SIDES], r1[k]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bmesh.ops.triangulate(bm, faces=bm.faces)
me = bpy.data.meshes.new('Chain')
bm.to_mesh(me)
bm.free()
chain = bpy.data.objects.new('Chain', me)
bpy.context.scene.collection.objects.link(chain)
a = me.attributes.new('vis', 'INT', 'FACE')
a.data.foreach_set('value', [1] * len(me.polygons))
groups['Chain'] = [chain]


def join(objs, name):
    for x in bpy.data.objects:
        x.select_set(x in objs)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = objs[0]; o.name = name; o.data.name = name; o.data.materials.clear()
    return o


P = {name: join(objs, name) for name, objs in groups.items()}


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


# tail
sh = P['Shorts']
bm = bmesh.new(); bm.from_mesh(sh.data); bm.verts.ensure_lookup_table()
co = np.array([tuple(v.co) for v in bm.verts])
side = (np.abs(co[:, 0]) > 0.09) & (np.abs(co[:, 0]) < 0.16)
cand = np.zeros(len(co), bool)
for i, c in enumerate(co):
    if abs(c[0]) >= 0.09 or c[2] < 0.28:
        continue
    near = side & (np.abs(co[:, 2] - c[2]) < 0.02)
    ref = co[near, 1].max() if near.any() else 0.0
    cand[i] = c[1] > ref + 0.01
# connected components of candidates; keep those reaching far behind (the tail tube)
seen = set(); tail = set()
for i in np.where(cand)[0]:
    if i in seen:
        continue
    comp = [i]; seen.add(i); st = [i]
    while st:
        x = st.pop()
        for e in bm.verts[x].link_edges:
            y = e.other_vert(bm.verts[x]).index
            if cand[y] and y not in seen:
                seen.add(y); comp.append(y); st.append(y)
    if co[comp, 1].max() > 0.25:
        tail.update(comp)
dead = [f for f in bm.faces if any(v.index in tail for v in f.verts)]
bmesh.ops.delete(bm, geom=dead, context='FACES')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
# fill the new hole(s) in the seat: boundary loops whose centre lies behind the seat near the midline
bm.edges.ensure_lookup_table()
bedges = [e for e in bm.edges if e.is_boundary]
loops = []; used = set()
for e in bedges:
    if e in used:
        continue
    comp = [e]; used.add(e); st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in used:
                    used.add(y); comp.append(y); st.append(y)
    vs = {v for x in comp for v in x.verts}
    c = sum((v.co for v in vs), Vector()) / len(vs)
    loops.append((comp, c, len(vs)))
filled = 0
for comp, c, n in loops:
    if abs(c.x) < 0.09 and c.y > 0.05 and c.z > 0.6:
        for v in bm.verts:
            v.tag = True                                    # pre-existing vertices
        loop = [comp[0].verts[0]]; prev = None              # walk the boundary loop in order
        while True:
            nxt = [e.other_vert(loop[-1]) for e in loop[-1].link_edges if e.is_boundary and e in comp]
            nxt = [v for v in nxt if v is not prev]
            if not nxt or nxt[0] is loop[0]:
                break
            prev = loop[-1]; loop.append(nxt[0])
        cap = bm.faces.new(loop)
        ring_co = {tuple(round(x, 6) for x in v.co) for v in loop}
        print('SEAT cap', len(loop), 'of', n)
        poked = bmesh.ops.poke(bm, faces=[cap])
        edges = list({e for f in poked['faces'] for e in f.edges if not (e.verts[0].tag and e.verts[1].tag)})
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
        inner = [v for v in bm.verts if not v.tag]
        # seat surface y = quadratic in (x, z), fitted to the ring and two rings of neighbours around it
        nb = {v for v in bm.verts if v.tag and tuple(round(x, 6) for x in v.co) in ring_co}
        for _ in range(2):
            nb |= {e.other_vert(v) for v in list(nb) for e in v.link_edges}
        fit = [v for v in nb if v.tag]
        A = np.array([[1, v.co.x, v.co.z, v.co.x ** 2, v.co.x * v.co.z, v.co.z ** 2] for v in fit])
        coef = np.linalg.lstsq(A, np.array([v.co.y for v in fit]), rcond=None)[0]
        for v in inner:
            v.co.y = float(np.dot([1, v.co.x, v.co.z, v.co.x ** 2, v.co.x * v.co.z, v.co.z ** 2], coef))
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
        print('SEAT patch verts', len(inner), 'fit from', len(fit))
        filled += n
        print('TAIL hole filled: %d boundary verts at %s' % (n, tuple(round(x, 3) for x in c)))
    elif n > 3:
        print('LOOP kept', n, tuple(round(x, 3) for x in c))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(sh.data); bm.free()
print('TAIL removed verts', len(tail), 'faces', len(dead))


def hidden_verts(o):
    vis = np.zeros(len(o.data.polygons), int); o.data.attributes['vis'].data.foreach_get('value', vis)
    seen = np.zeros(len(o.data.vertices), bool)
    for p in o.data.polygons:
        if vis[p.index]:
            seen[list(p.vertices)] = True
    return ~seen


def decimate(o, passes):
    """passes: [(face predicate(centre, all_verts_hidden, touches_boundary), ratio)]"""
    for x in bpy.data.objects:
        x.select_set(x == o)
    bpy.context.view_layer.objects.active = o
    for pred, ratio in passes:
        h = hidden_verts(o)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bnd = {v.index for e in bm.edges if e.is_boundary for v in e.verts}
        flags = [pred(f.calc_center_median(), all(h[v.index] for v in f.verts), any(v.index in bnd for v in f.verts))
                 for f in bm.faces]
        bm.free()
        o.data.polygons.foreach_set('select', flags)
        o.data.update()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.decimate(ratio=ratio)
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')


HEAD = lambda c: c.z > 1.26
HAND = lambda c: c.z < 0.92 and abs(c.x) > 0.33
decimate(P['Body'], [(lambda c, h, b: h and not b and not HEAD(c), 0.3),
                     (lambda c, h, b: not h and not b and not HEAD(c) and not HAND(c), 0.6)])
decimate(P['Shorts'], [(lambda c, h, b: h and not b, 0.3), (lambda c, h, b: not h and not b, 0.6)])
decimate(P['Leg'], [(lambda c, h, b: h and not b, 0.3), (lambda c, h, b: not h and not b, 0.6)])
decimate(P['Foot'], [(lambda c, h, b: not b, 0.5)])
decimate(P['Teeth'], [(lambda c, h, b: True, 0.4)])
decimate(P['Tongue'], [(lambda c, h, b: h, 0.3), (lambda c, h, b: not h, 0.6)])
decimate(P['Pendant'], [(lambda c, h, b: True, 0.5)])

after = {n: tris(o) for n, o in P.items()}
ORDER = ['Body', 'Shorts', 'Leg', 'Foot', 'Pendant', 'Chain', 'Teeth', 'Tongue', 'Mane', 'Fur']
for n in ORDER:
    o = P[n]
    o.data.attributes.remove(o.data.attributes['vis'])
    a = o.data.attributes.new('part', 'INT', 'FACE')
    a.data.foreach_set('value', [ORDER.index(n)] * len(o.data.polygons))
    for p in o.data.polygons:
        p.use_smooth = True
for x in bpy.data.objects:
    x.select_set(x.type == 'MESH')
bpy.context.view_layer.objects.active = P['Body']
bpy.ops.object.join()
g = bpy.context.view_layer.objects.active
g.name = 'Werewolf'
g.data.name = 'Werewolf'
bpy.context.scene['wfigt1_parts'] = json.dumps(ORDER)
report = {'before': before, 'after': after, 'total_after': sum(after.values()), 'tail_verts': len(tail), 'hidden_cards_dropped': hidden_cards}
json.dump(report, open(os.path.join(common.WORK, 'step1_report.json'), 'w'), indent=1)
print('STEP1', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
