"""Step 1 cleanup for the MM6 cleric (Smart Topology v1, A-pose, left fist and loosely closed right hand, open cloak).

Input work/v1_vis.blend (normalised 1.578 m, soles z=0, facing -Y; loose parts with per-face outside visibility from
analyse_parts.py). Parts (examine_parts.py, review/v1_parts_sheet.png): P00 collar + mantle + cloak (one thick
shell, open at the front, a 5-vertex tear at the back hem), P01 tunic with sleeves, hands and neck, P02 trousers and
boots, P03 face, P04 hair, P05 belt tongue; P06 the chest emblem disc (painted instead), P07/P08 eyeballs are deleted.
- Decimation in edit mode on selected faces only: the face, the hands, the collar/neck and part boundaries keep every
  vertex; hidden faces go hardest (kept, not deleted: they can show while the cloak moves).
- Hidden skin/cloth within 8 mm of a covering shell is tucked under it (tunic under the mantle, legs under the
  tunic skirt, face under hair and collar).
Joins everything into one mesh 'Cleric' with a per-face 'part' attribute (index into scene['cle_parts']).
Saves work/step1_v1.blend."""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'v1_vis.blend'))
O = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
NAMED = {'P00': 'Cloak', 'P01': 'Torso', 'P02': 'Legs', 'P03': 'Head', 'P04': 'Hair', 'P05': 'Belt'}
P = {}
for n, o in list(O.items()):
    if n not in NAMED:
        bpy.data.objects.remove(o, do_unlink=True)
        continue
    a = o.data.attributes.new('vis', 'INT', 'FACE')
    a.data.foreach_set('value', [int(x) for x in o['visible']])
    del o['visible']
    o.name = o.data.name = NAMED[n]
    o.data.materials.clear()
    P[NAMED[n]] = o


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


before = {n: tris(o) for n, o in P.items()}

# the small tear at the back of the cloak hem: fill it
bm = bmesh.new(); bm.from_mesh(P['Cloak'].data)
small = [e for e in bm.edges if e.is_boundary and all(v.co.z < 0.3 for v in e.verts)]
filled = bmesh.ops.contextual_create(bm, geom=small)['faces']  # holes_fill skips this non-convex loop
bmesh.ops.triangulate(bm, faces=filled)
vl = bm.faces.layers.int['vis']
for f in filled:
    f[vl] = 1
bm.to_mesh(P['Cloak'].data); bm.free()


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


COLLAR = lambda c: c.z > 1.30
HANDS = lambda c: c.z < 0.97 and abs(c.x) > 0.19
decimate(P['Cloak'], [(lambda c, h, b: h and not b and not COLLAR(c), 0.3),
                      (lambda c, h, b: not h and not b and not COLLAR(c), 0.5)])
decimate(P['Torso'], [(lambda c, h, b: h and not b, 0.3),
                      (lambda c, h, b: not h and not b and not COLLAR(c) and not HANDS(c), 0.55)])
decimate(P['Legs'], [(lambda c, h, b: h and not b, 0.3), (lambda c, h, b: not h and not b, 0.5)])
decimate(P['Head'], [(lambda c, h, b: h and not b, 0.4)])
decimate(P['Hair'], [(lambda c, h, b: h and not b, 0.4), (lambda c, h, b: not h and not b and c.y > -0.05, 0.75)])
decimate(P['Belt'], [(lambda c, h, b: not b, 0.35)])


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
          (('Torso', 'Cloak', (1.0, 1.45)), ('Legs', 'Torso', (0.35, 1.0)), ('Head', 'Hair', (1.35, 1.60)),
           ('Head', 'Cloak', (1.25, 1.40)), ('Torso', 'Belt', (0.80, 1.0)))}
after = {n: tris(o) for n, o in P.items()}
ORDER = ['Torso', 'Cloak', 'Legs', 'Head', 'Hair', 'Belt']
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
g.name = 'Cleric'
g.data.name = 'Cleric'
bpy.context.scene['cle_parts'] = json.dumps(ORDER)
report = {'before': before, 'after': after, 'total_after': sum(after.values()), 'cloak_tear_faces': len(filled),
          'tucked_verts': tucked}
json.dump(report, open(os.path.join(common.WORK, 'step1_report.json'), 'w'), indent=1)
print('STEP1', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
