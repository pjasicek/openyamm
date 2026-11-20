"""The Glassback Queen's crown (boss_glassback_queen.png, candidate 3): a coronet of upright faceted glass spines on
the skull, built with the family's crystals.py on the Glassback's rest pose, one rigid attachment on Head.
Args: -- <crest blend (work/source_crest_v3.blend, a copy of hes_glassback_claude/work/crest_v3.blend)> <out.blend>

Layout (rest pose, metres at tier A size; forward -Y): the skull top is at y -1.25, z 0.88; the head runs from the
neck (y -1.16) to the beak (y -1.50), 0.47 m wide. Nine spines stand on an ellipse round the crown of the skull
(centre y -1.245, half-axes 0.15 across, 0.11 along), the tallest at the back and the sides, smaller toward the front
so the eyes and beak stay clear; each splays out to the side (the concept's slightly splayed coronet), the rear ones upright. Objects Crown_Head[_LOD1..3] parented to Head. LODs as the crest: 1 no cracks and at most 5 sides;
2 no seams, 4 sides, the three smallest dropped; 3 three sides, only the five largest."""
import bpy, os, sys, math, random
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import crystals

src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=C.path(src))
rig = bpy.data.objects[C.RIG]; body = bpy.data.objects[C.MESH]
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())


def hide_hit(origin, direction):
    return bvh.ray_cast(Vector(origin), Vector(direction).normalized(), 1.0)[0]


CENTRE = Vector((0.0, -1.25, 0.0))
RX, RY = 0.165, 0.125
# (angle round the ring from the back, degrees; positive toward the creature's left (+x); height m)
SPINES = [(0, 0.38), (36, 0.36), (-36, 0.36), (74, 0.33), (-74, 0.33), (112, 0.25), (-112, 0.25),
          (148, 0.16), (-148, 0.16)]
RADIUS = 0.52

placed = []
for i, (ang, h) in enumerate(SPINES):
    a = math.radians(ang)
    x, y = CENTRE.x + RX * math.sin(a), CENTRE.y + RY * math.cos(a)       # angle 0 = back of the ring (+y)
    hit = bvh.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)))
    if hit[0] is None:
        print('CROWN miss', ang); continue
    p, n = hit[0], hit[1].normalized()
    # splay outward to the sides only a little toward the back: a backward rake put the rear tips into the crest's
    # first plate when the head tips up (crown_check.py)
    out = Vector((math.sin(a), math.cos(a) * 0.25, 0)).normalized()
    axis = (Vector((0, 0, 1)) * 0.80 + n * 0.10 + out * 0.28 + Vector((0, -0.04, 0))).normalized()
    placed.append(dict(p=p, axis=axis, h=h, seed=100 + i, sides=6 if h > 0.2 else 5))
print('CROWN spines', len(placed), 'roots z', [round(c['p'].z, 3) for c in placed])

import json as _json
_json.dump([{'p': list(c['p']), 'axis': list(c['axis']), 'h': c['h'], 'bone': 'Head',
             'radius': max(0.035, min(0.15, RADIUS * c['h'] * 0.6))} for c in placed],
           open(C.path('work/crown_layout.json'), 'w'), indent=0)
glass = bpy.data.materials.get('Glass') or bpy.data.materials.new('Glass')
glow = bpy.data.materials.get('Glow') or bpy.data.materials.new('Glow')
order = sorted(range(len(placed)), key=lambda k: -placed[k]['h'])
for lod in range(4):
    bm = bmesh.new()
    for k, c in enumerate(placed):
        if lod >= 2 and k not in order[:len(placed) - 3]:
            continue
        if lod >= 3 and k not in order[:5]:
            continue
        r = random.Random(c['seed'] * 7 + 1)
        radius = max(0.035, min(0.15, RADIUS * c['h'] * 0.6))
        sides = {0: c['sides'], 1: min(c['sides'], 5), 2: 4, 3: 3}[lod]
        crystals.crystal(bm, c['p'], c['axis'], c['h'], radius, sides, r, lod=lod,
                         crack_count=3 if c['h'] > 0.2 else 2, seam=lod <= 1, twist=r.uniform(-0.3, 0.3),
                         edge_glow=2 if c['h'] > 0.15 else 1, hide_hit=hide_hit)
    name = 'Crown_Head' + (f'_LOD{lod}' if lod else '')
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh); bm.free()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    mesh.materials.append(glass); mesh.materials.append(glow)
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = 'Head'
    bpy.context.view_layer.update()
    ob.matrix_world = Matrix.Identity(4)
    print('CROWN LOD', lod, 'tris', sum(len(p.vertices) - 2 for p in mesh.polygons))

# The neck gap (candidate 3: bare hide between the crown and the crest): the tall crest's two frontmost midline plates
# (layout y -0.975 and -0.778, on Spine3; the second met the crown's rear spines when the head tips up in Bite and
# Death, crown_check.py) are removed from Crest_tall_Spine3 and its LODs. Every crest face goes to the crystal
# whose axis segment is nearest its centre (work/crest_layout.json, copied from hes_glassback_claude/work/).
import json
layout = json.load(open(C.path('work/crest_layout.json')))
def dropped(c):
    return c['bone'] == 'Spine3' and (c['p'][1] < -0.9 or (c['row'] == 'mid' and c['p'][1] < -0.7))


DROP = [c for c in layout if dropped(c)]
KEEP = [c for c in layout if c['bone'] == 'Spine3' and not dropped(c)]


def seg_dist(q, c, hs=1.3):
    a = Vector(c['p']) - Vector(c['axis']) * c['radius'] * 1.3
    b = Vector(c['p']) + Vector(c['axis']) * c['h'] * hs
    ab = b - a
    t = max(0.0, min(1.0, (q - a).dot(ab) / ab.length_squared))
    return (q - (a + ab * t)).length - c['radius'] * 0.5


for ob in [o for o in bpy.data.objects if o.name.startswith('Crest_tall_Spine3')]:
    bm = bmesh.new(); bm.from_mesh(ob.data)
    mw = ob.matrix_world
    gone = [f for f in bm.faces if min(seg_dist(mw @ f.calc_center_median(), c) for c in DROP)
            < min(seg_dist(mw @ f.calc_center_median(), c) for c in KEEP)]
    n0 = len(bm.faces)
    bmesh.ops.delete(bm, geom=gone, context='FACES')
    bm.to_mesh(ob.data); bm.free()
    print('CREST_TRIM', ob.name, n0, '->', len(ob.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=C.path(dst))
