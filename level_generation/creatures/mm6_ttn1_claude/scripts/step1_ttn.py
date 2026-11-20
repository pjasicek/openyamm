"""Step 1 cleanup for the MM6 titan (Smart Topology v1, open hands, A-pose).

Input work/st1_vis.blend (normalised 1.578 m, soles z=0, facing -Y; loose parts with per-face outside visibility from
analyse_parts.py). Parts (examine_parts.py, review/st1_parts_*.png): P00 body (torso, arms, hands, neck, head skin),
P01 legs and feet (with the left greave), P02 helmet shell with cheek guards, P03 crest (an open sheet), P04 helmet
dome, P05/P06 pauldrons, P07 right greave, P08/P09 bracers, P10 belt, P11/P12 bracer top bands, P13/P15 knee caps,
P14 nape under the helmet, P16/P21 eyeballs, P18/P30 belt medallion, P22/P23 helmet ear bosses, the other parts of
30-100 triangles below the belt are skirt scales, and parts under 20 vertices are rivets.

- Rivets (about 1.3k triangles of tiny spheres), the eyeballs and two stray triangles are deleted: rivets and the
  blank white eyes come from the texture.
- Decimation in edit mode on selected faces only: face/head (z > 1.29), hands and part boundaries keep every vertex;
  hidden faces go hardest (they are kept, not deleted: skin under the pauldrons and bracers moves in the clips).
- Skin holes of up to 10 edges are filled (a tear at the right mouth corner).
- Hidden skin within 8 mm of an armour shell is tucked under it so it cannot poke through after decimation.
Joins everything into one mesh 'Titan' with a per-face 'part' attribute (index into scene['ttn_parts']).
Saves work/step1_v1.blend."""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st1_vis.blend'))
O = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
NAMED = {'P00': 'Body', 'P01': 'Legs', 'P02': 'Helmet', 'P03': 'Crest', 'P04': 'Dome', 'P05': 'Pauldron',
         'P06': 'Pauldron', 'P07': 'Greave', 'P08': 'Bracer', 'P09': 'Bracer', 'P10': 'Belt', 'P11': 'Band',
         'P12': 'Band', 'P13': 'Knee', 'P15': 'Knee', 'P14': 'Nape', 'P18': 'Belt', 'P30': 'Belt', 'P22': 'Helmet',
         'P23': 'Helmet'}
DROP = {'P16', 'P21', 'P108', 'P109'}
groups = {}
for n, o in list(O.items()):
    if n in DROP or (n not in NAMED and len(o.data.vertices) < 20):
        bpy.data.objects.remove(o, do_unlink=True)
        continue
    a = o.data.attributes.new('vis', 'INT', 'FACE')          # survives the joins below (polygon order does not)
    a.data.foreach_set('value', [int(x) for x in o['visible']])
    del o['visible']
    groups.setdefault(NAMED.get(n, 'Skirt'), []).append(o)
before = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for g in groups.values() for o in g)


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


def hidden_verts(o):
    vis = np.zeros(len(o.data.polygons), int); o.data.attributes['vis'].data.foreach_get('value', vis)
    seen = np.zeros(len(o.data.vertices), bool)
    for p in o.data.polygons:
        if vis[p.index]:
            seen[list(p.vertices)] = True
    return ~seen


for o in P.values():
    a = o.data.attributes.new('hid', 'FLOAT', 'POINT')
    a.data.foreach_set('value', hidden_verts(o).astype(float))


def hid(o):
    h = np.zeros(len(o.data.vertices))
    o.data.attributes['hid'].data.foreach_get('value', h)
    return h > 0.5


def decimate(o, passes):
    """passes: [(face predicate(centre, all_verts_hidden, touches_boundary), ratio)]"""
    for x in bpy.data.objects:
        x.select_set(x == o)
    bpy.context.view_layer.objects.active = o
    for pred, ratio in passes:
        h = hid(o)
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


HEAD = lambda c: c.z > 1.29
HAND = lambda c: c.z < 0.75 and abs(c.x) > 0.30
FOOT = lambda c: c.z < 0.07
decimate(P['Body'], [(lambda c, h, b: h and not b and not HEAD(c), 0.3),
                     (lambda c, h, b: not h and not b and not HEAD(c) and not HAND(c), 0.6)])
decimate(P['Legs'], [(lambda c, h, b: h and not b, 0.3),
                     (lambda c, h, b: not h and not b and not FOOT(c), 0.6)])
for n, r in (('Skirt', 0.6), ('Crest', 0.6), ('Pauldron', 0.6), ('Greave', 0.6), ('Bracer', 0.7), ('Knee', 0.7),
             ('Helmet', 0.8), ('Dome', 0.7), ('Nape', 0.5)):
    decimate(P[n], [(lambda c, h, b: h and not b, 0.3), (lambda c, h, b, r=r: not h and not b, r)])


def tuck(inner, outer, gap, zr, back=0.02):
    """Inner-shell hidden vertices just outside (< gap) or slightly through (< back) the outer shell move to gap
    below it."""
    o = P[outer]
    me = P[inner].data
    tree = BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons])
    me.update()
    moved = 0
    h = hid(P[inner])
    for v in me.vertices:
        if not h[v.index] or not (zr[0] < v.co.z < zr[1]):
            continue
        n = v.normal.copy()
        out = tree.ray_cast(v.co + n * 1e-5, n, gap)
        inn = tree.ray_cast(v.co - n * 1e-5, -n, back)
        if out[0] is not None:
            v.co = out[0] - n * gap
            moved += 1
        elif inn[0] is not None:
            v.co = inn[0] - n * gap
            moved += 1
    me.update()
    return moved


tucked = {f'{a}<{b}': tuck(a, b, 0.008, zr) for a, b, zr in
          (('Body', 'Pauldron', (1.05, 1.40)), ('Body', 'Bracer', (0.70, 1.00)), ('Body', 'Band', (0.80, 1.00)),
           ('Body', 'Belt', (0.78, 0.92)), ('Legs', 'Greave', (0.05, 0.40)), ('Legs', 'Knee', (0.28, 0.45)),
           ('Body', 'Helmet', (1.25, 1.50)), ('Nape', 'Helmet', (1.25, 1.50)))}

# small tears in the skin (a 5-edge hole at the right mouth corner): filled
bm = bmesh.new(); bm.from_mesh(P['Body'].data)
filled = []
seen = set()
for e in [e for e in bm.edges if e.is_boundary]:
    if e in seen:
        continue
    ring = [e.verts[0]]; prev = None; cur = e                 # walk the boundary loop
    while True:
        seen.add(cur); nxt_v = cur.other_vert(ring[-1])
        if nxt_v is ring[0]:
            break
        ring.append(nxt_v)
        cand = [x for x in nxt_v.link_edges if x.is_boundary and x is not cur and x not in seen]
        if not cand or len(ring) > 10:
            ring = []; break
        cur = cand[0]
    if 3 <= len(ring) <= 10:
        try:
            filled.append(bm.faces.new(ring))
        except ValueError:
            pass
bmesh.ops.triangulate(bm, faces=filled); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(P['Body'].data); bm.free()
tucked['filled_faces'] = len(filled)
after = {n: tris(o) for n, o in P.items()}
ORDER = ['Body', 'Legs', 'Skirt', 'Belt', 'Pauldron', 'Bracer', 'Band', 'Greave', 'Knee', 'Helmet', 'Dome', 'Crest',
         'Nape']
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
g.name = 'Titan'
g.data.name = 'Titan'
bpy.context.scene['ttn_parts'] = json.dumps(ORDER)
report = {'before': before, 'after': after, 'total_after': sum(after.values()), 'tucked_verts': tucked}
json.dump(report, open(os.path.join(common.WORK, 'step1_report.json'), 'w'), indent=1)
print('STEP1', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
