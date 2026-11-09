"""Step 1 for the goblin: classify the Meshy Smart Topology shells, drop eyeballs/fragments, decimate cheap parts
(spikes, hoops, teeth, skirt strips, hidden skin) and join into named parts:
Body, Teeth, Hoops, Armor (gorget/pauldrons/bracers/greaves), Spikes, Leather (belt/pouch/strips/straps).
Output work/step1_v1.blend + review renders."""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

common.clear_scene()
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, 'meshy/smart_topology_v1/model_urls_glb.glb'))
obj = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in bpy.data.objects:
    o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in obj.data.vertices])
s = 1.578 / (co[:, 2].max() - co[:, 2].min())
obj.scale = (s, s, s)
obj.location = (-(co[:, 0].max() + co[:, 0].min()) / 2 * s, -(co[:, 1].max() + co[:, 1].min()) / 2 * s, -co[:, 2].min() * s)
bpy.ops.object.transform_apply(location=True, scale=True)
obj.data.materials.clear()
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def classify(o):
    c = np.array([tuple(v.co) for v in o.data.vertices]); n = len(c)
    lo, hi = c.min(0), c.max(0); ext = hi - lo; mid = c.mean(0)
    if n > 2000:
        return 'Body'
    if n < 10:
        return 'Drop'
    if 1.40 < mid[2] < 1.46 and mid[1] < -0.09 and n < 120:
        return 'Drop'                                          # eyeballs (painted)
    if 1.32 < mid[2] < 1.40 and mid[1] < -0.07 and abs(mid[0]) < 0.08:
        return 'Teeth'
    if 1.34 < mid[2] < 1.45 and abs(mid[0]) > 0.09:
        return 'Hoops'
    if n < 30 and max(ext) < 0.08:
        return 'Spikes' if max(ext) > 0.03 else 'Leather'      # tiny rivets/studs -> leather
    if max(ext) < 0.09 and 25 <= n <= 30:
        return 'Spikes'
    if 0.55 < mid[2] < 0.90 and ext[0] < 0.14 and ext[2] > 0.15:
        return 'Leather'                                       # skirt strips
    if 0.74 < mid[2] < 0.93:
        return 'Leather'                                       # belt, pouch, buckle
    if 0.03 < mid[2] < 0.46 and ext[2] < 0.12 and n < 60:
        return 'Leather'                                       # greave straps/studs
    return 'Armor'


groups = {}
before = 0
for o in list(bpy.data.objects):
    if o.type != 'MESH':
        continue
    before += tris(o)
    k = classify(o)
    if k == 'Drop':
        bpy.data.objects.remove(o, do_unlink=True)
        continue
    groups.setdefault(k, []).append(o)
print('CLASSES', {k: (len(v), sum(tris(o) for o in v)) for k, v in groups.items()})


def decimate(o, ratio, weight_fn=None):
    m = o.modifiers.new('Decimate', 'DECIMATE'); m.ratio = ratio; m.use_collapse_triangulate = True
    if weight_fn:
        g = o.vertex_groups.new(name='w')
        for v in o.data.vertices:
            g.add([v.index], float(weight_fn(v)), 'REPLACE')
        m.vertex_group = 'w'
    bpy.context.view_layer.objects.active = o
    for x in bpy.data.objects:
        x.select_set(x == o)
    bpy.ops.object.modifier_apply(modifier=m.name)
    if 'w' in o.vertex_groups:
        o.vertex_groups.remove(o.vertex_groups['w'])


for o in groups.get('Spikes', []):
    decimate(o, 0.45)
for o in groups.get('Hoops', []):
    decimate(o, 0.30)
for o in groups.get('Teeth', []):
    decimate(o, 0.40)
for o in groups.get('Leather', []):
    if tris(o) > 60:
        decimate(o, 0.55)
for o in groups.get('Armor', []):
    decimate(o, 0.75)

joined = {}
for k, objs in groups.items():
    for x in bpy.data.objects:
        x.select_set(x in objs)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = k; o.data.name = k
    for p in o.data.polygons:
        p.use_smooth = True
    joined[k] = o

# hidden skin: body faces covered by armor/leather (outward ray hits within 4 cm) carry no visual detail
cover_objs = [joined[k] for k in ('Armor', 'Leather') if k in joined]
verts, polys = [], []
for o in cover_objs:
    base = len(verts)
    verts += [v.co.copy() for v in o.data.vertices]
    polys += [tuple(base + i for i in p.vertices) for p in o.data.polygons]
cover = BVHTree.FromPolygons(verts, polys)
body = joined['Body']
body.data.update()


def body_weight(v):
    c = v.co
    if c.z > 1.30 and c.y < -0.02:
        return 0.0                                             # face
    if abs(c.x) > 0.40 and c.z < 0.95:
        return 0.15                                            # hands/claws
    if c.z < 0.06:
        return 0.35                                            # feet
    h = cover.ray_cast(c + v.normal * 1e-4, v.normal, 0.04)
    return 1.0 if h[0] is not None else 0.35


decimate(body, 0.72, body_weight)
after = {k: tris(o) for k, o in joined.items()}
report = {'before': before, 'after': after, 'total_after': sum(after.values())}
json.dump(report, open(os.path.join(common.WORK, 'step1_report.json'), 'w'), indent=1)
print('STEP1', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
scene = bpy.context.scene
common.workbench_clay(scene); scene.display.shading.color_type = 'RANDOM'
common.render_views(os.path.join(common.REVIEW, 'step1'), 0.8, 1.7, views=('front', 'three_quarter', 'left', 'back'),
                    resolution=(500, 750))
scene.display.shading.color_type = 'SINGLE'
common.render_views(os.path.join(common.REVIEW, 'step1_head'), 1.40, 0.32, views=('front', 'left'), resolution=(450, 450))
common.render_views(os.path.join(common.REVIEW, 'step1_feet'), 0.12, 0.40, views=('front', 'left'), resolution=(450, 450))
common.render_views(os.path.join(common.REVIEW, 'step1_hand'), 0.78, 0.28, views=('front', 'left'), resolution=(450, 450), target=(-0.5, 0))
