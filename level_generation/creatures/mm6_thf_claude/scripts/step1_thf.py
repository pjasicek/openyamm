"""Step 1 cleanup for the MM6 thief (Smart Topology v1, A-pose with loosely closed hands, open cloak).

Input work/st1_vis.blend (normalised 1.578 m, soles z=0, facing -Y; loose parts with per-face outside visibility from
analyse_parts.py). Parts (examine_parts.py, review/st1_parts_sheet.png): P00 torso (jerkin top, sleeves, neck),
P01 hood + mantle + cloak (one closed thick shell, open at the front), P02 jerkin skirt, P03 legs, P04/P05 right/left
hand shells, P06/P07 left/right boot, P08 face, P09 sheath, P10 pouch, P11 strap, P12/P13 right/left bracer,
P17 buckle, P18 hilt cap; P14/P15 eyeballs, P16 a chest clasp (not in the native design) and P19/P20 hidden specks
are deleted.
- Decimation in edit mode on selected faces only: the face, the hood (z > 1.33) and part boundaries keep every
  vertex; hidden faces go hardest (kept, not deleted: they can show while the cloak moves), including the skull under
  the hood (part of the torso shell).
- Hidden face faces behind the hood (two rings from any visible face) are deleted: the hood follows the head.
- Hidden skin/cloth within 8 mm of a covering shell is tucked under it (torso under the mantle, bracers and strap,
  legs under the skirt and boots).
Joins everything into one mesh 'Thief' with a per-face 'part' attribute (index into scene['thf_parts']).
Saves work/step1_v1.blend."""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st1_vis.blend'))
O = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
NAMED = {'P00': 'Torso', 'P01': 'Cloak', 'P02': 'Skirt', 'P03': 'Legs', 'P04': 'Hand', 'P05': 'Hand',
         'P06': 'Boot', 'P07': 'Boot', 'P08': 'Head', 'P09': 'Sheath', 'P10': 'Pouch', 'P11': 'Strap',
         'P12': 'Bracer', 'P13': 'Bracer', 'P17': 'Buckle', 'P18': 'Sheath'}
groups = {}
for n, o in list(O.items()):
    if n not in NAMED:
        bpy.data.objects.remove(o, do_unlink=True)
        continue
    a = o.data.attributes.new('vis', 'INT', 'FACE')
    a.data.foreach_set('value', [int(x) for x in o['visible']])
    del o['visible']
    groups.setdefault(NAMED[n], []).append(o)
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


# hidden face faces (behind/inside the hood) more than two rings from a visible face: deleted
bm = bmesh.new(); bm.from_mesh(P['Head'].data); bm.faces.ensure_lookup_table()
vl = bm.faces.layers.int['vis']
keep = {f for f in bm.faces if f[vl]}
for _ in range(2):
    keep |= {g for f in keep for v in f.verts for g in v.link_faces}
gone = [f for f in bm.faces if f not in keep]
bmesh.ops.delete(bm, geom=gone, context='FACES')
bm.to_mesh(P['Head'].data); bm.free()
head_deleted = len(gone)


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


HOOD = lambda c: c.z > 1.33
NECKWRIST = lambda c: c.z > 1.33 or (c.z < 0.90 and abs(c.x) > 0.20)
decimate(P['Cloak'], [(lambda c, h, b: h and not b and not HOOD(c), 0.3),
                      (lambda c, h, b: not h and not b and not HOOD(c), 0.55)])
decimate(P['Torso'], [(lambda c, h, b: h and not b, 0.3),
                      (lambda c, h, b: not h and not b and not NECKWRIST(c), 0.6)])
decimate(P['Legs'], [(lambda c, h, b: h and not b, 0.3), (lambda c, h, b: not h and not b, 0.6)])
for n, r in (('Skirt', 0.6), ('Hand', 0.7), ('Boot', 0.5), ('Sheath', 0.45), ('Pouch', 0.5), ('Strap', 0.6),
             ('Bracer', 0.7)):
    decimate(P[n], [(lambda c, h, b: h and not b, 0.3), (lambda c, h, b, r=r: not h and not b, r)])


def tuck(inner, outer, gap, zr, back=0.02):
    """Hidden inner-shell vertices just outside (< gap) or slightly through (< back) the outer shell move to gap
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
          (('Torso', 'Cloak', (1.0, 1.60)), ('Torso', 'Bracer', (0.78, 0.92)), ('Torso', 'Strap', (0.90, 1.20)),
           ('Torso', 'Skirt', (0.85, 1.00)), ('Legs', 'Skirt', (0.70, 0.95)), ('Legs', 'Boot', (0.05, 0.25)),
           ('Head', 'Cloak', (1.33, 1.60)))}
after = {n: tris(o) for n, o in P.items()}
ORDER = ['Torso', 'Cloak', 'Skirt', 'Legs', 'Hand', 'Boot', 'Head', 'Sheath', 'Pouch', 'Strap', 'Bracer', 'Buckle']
for n in ORDER:
    o = P[n]
    o.data.attributes.remove(o.data.attributes['vis'])
    a = o.data.attributes.new('part', 'INT', 'FACE')
    a.data.foreach_set('value', [ORDER.index(n)] * len(o.data.polygons))
    for p in o.data.polygons:
        p.use_smooth = True
for x in bpy.data.objects:
    x.select_set(x.type == 'MESH')
bpy.context.view_layer.objects.active = P['Torso']
bpy.ops.object.join()
g = bpy.context.view_layer.objects.active
g.name = 'Thief'
g.data.name = 'Thief'
bpy.context.scene['thf_parts'] = json.dumps(ORDER)
report = {'before': before, 'after': after, 'total_after': sum(after.values()), 'head_faces_deleted': head_deleted,
          'tucked_verts': tucked}
json.dump(report, open(os.path.join(common.WORK, 'step1_report.json'), 'w'), indent=1)
print('STEP1', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
