"""Step 1 cleanup for the MM6 guard (Smart Topology v1, closed fists, coif repaired by coif_repair.py).

Input work/st1r_vis.blend (normalised 1.578 m, soles z=0, facing -Y; parts with per-face outside visibility from
analyse_parts.py). Parts: P00 mail shirt + sleeves + neck, P01 legs + shoes, P02 coif, P03 face/skull,
P04/P05 arms with fists (character right = -X), P06 helmet, P08 nasal bar.

- Face/skull and coif: faces never seen from outside are deleted (one-ring margin kept); the head is rigid.
- Decimation in edit mode on selected faces only, so the eye window, fists, rims and boundaries keep every vertex.
- Hidden skin within 8 mm of an outer shell is tucked under it (arms in sleeves, legs under the hem, neck in the
  coif) so it cannot poke through after decimation.
Joins everything into one mesh 'Guard' with a per-face 'part' attribute (index into scene['gua_parts']).
Saves work/step1_v1.blend."""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st1r_vis.blend'))
NAMES = {'P00': 'Shirt', 'P01': 'Legs', 'P02': 'Coif', 'P03': 'Head', 'P06': 'Helmet', 'P08': 'Nasal'}
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    c = np.array([tuple(v.co) for v in o.data.vertices]).mean(0)
    if o.name in ('P04', 'P05'):
        o.name = 'ArmRight' if c[0] < 0 else 'ArmLeft'
    else:
        o.name = NAMES[o.name]
    o.data.materials.clear()
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


before = sum(tris(o) for o in P.values())


def hidden_verts(o):
    vis = list(o['visible'])
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


def drop_hidden(o, keep=lambda c: False):
    vis = list(o['visible'])
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    seen = {f.index for f in bm.faces if vis[f.index] or keep(f.calc_center_median())}
    seen |= {g.index for f in bm.faces if f.index in seen for e in f.edges for g in e.link_faces}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in seen], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    del o['visible']


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


EYES = lambda c: 1.385 < c.z < 1.465 and c.y < 0.0 and abs(c.x + 0.006) < 0.075
drop_hidden(P['Head'], keep=EYES)
drop_hidden(P['Coif'])
decimate(P['Head'], [(lambda c, h, b: not b and not EYES(c), 0.5)])
decimate(P['Coif'], [(lambda c, h, b: not b and not (1.37 < c.z < 1.48 and c.y < 0.0), 0.6)])
decimate(P['Helmet'], [(lambda c, h, b: h and not b, 0.25), (lambda c, h, b: not h and not b, 0.5)])
decimate(P['Nasal'], [(lambda c, h, b: not b, 0.5)])
decimate(P['Shirt'], [(lambda c, h, b: h and not b, 0.3),
                      (lambda c, h, b: not h and not b and c.z < 1.30, 0.6)])
decimate(P['Legs'], [(lambda c, h, b: h and not b, 0.3),
                     (lambda c, h, b: not h and not b and c.z < 0.10, 0.5),           # shoes
                     (lambda c, h, b: not h and not b and c.z >= 0.10, 0.6)])         # trousers
for n in ('ArmRight', 'ArmLeft'):
    decimate(P[n], [(lambda c, h, b: not b and abs(c.x) < 0.47, 0.55)])                 # fists (|x| > 0.47) kept


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


tucked = {'ArmRight<Shirt': tuck('ArmRight', 'Shirt', 0.008, (0.8, 1.3)),
          'ArmLeft<Shirt': tuck('ArmLeft', 'Shirt', 0.008, (0.8, 1.3)),
          'Legs<Shirt': tuck('Legs', 'Shirt', 0.008, (0.6, 0.8)),
          'Shirt<Coif': tuck('Shirt', 'Coif', 0.006, (1.25, 1.45)),
          'Head<Coif': tuck('Head', 'Coif', 0.005, (1.28, 1.40))}

after = {n: tris(o) for n, o in P.items()}
ORDER = ['Shirt', 'Legs', 'ArmRight', 'ArmLeft', 'Head', 'Coif', 'Helmet', 'Nasal']
for n in ORDER:
    o = P[n]
    if 'visible' in o.keys():
        del o['visible']
    a = o.data.attributes.new('part', 'INT', 'FACE')
    a.data.foreach_set('value', [ORDER.index(n)] * len(o.data.polygons))
    for p in o.data.polygons:
        p.use_smooth = True
for x in bpy.data.objects:
    x.select_set(x.type == 'MESH')
bpy.context.view_layer.objects.active = P['Shirt']
bpy.ops.object.join()
g = bpy.context.view_layer.objects.active
g.name = 'Guard'
g.data.name = 'Guard'
bpy.context.scene['gua_parts'] = json.dumps(ORDER)
report = {'before': before, 'after': after, 'total_after': sum(after.values()), 'tucked_verts': tucked}
json.dump(report, open(os.path.join(common.WORK, 'step1_report.json'), 'w'), indent=1)
print('STEP1', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
