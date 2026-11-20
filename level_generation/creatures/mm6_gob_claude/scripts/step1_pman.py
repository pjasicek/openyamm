"""Step 1 for the male peasant: name the Meshy Smart Topology parts, drop eyeballs/mouth interior/fragments
(eyes are painted later), smooth the knee crease and decimate only where detail is cheap (boots, thighs under
the tunic, skull under hair, flat tunic back, belt/buckle). Output work/step1_v1.blend with parts
Body (head+neck+arms), Tunic, Legs (trousers+boots), Hair, Belt, Buckle."""
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


parts = {}
before = 0
for o in list(bpy.data.objects):
    if o.type != 'MESH':
        continue
    c = np.array([tuple(v.co) for v in o.data.vertices]); n = len(c)
    lo, hi = c.min(0), c.max(0)
    before += tris(o)
    if n > 1000 and lo[2] < 0.01:
        name = 'Legs'
    elif n > 1000 and lo[2] > 1.2:
        name = 'Head'
    elif n > 1000:
        name = 'Tunic'
    elif n > 500 and abs(c[:, 0].mean()) > 0.2:
        name = 'ArmLeft' if c[:, 0].mean() > 0 else 'ArmRight'
    elif n > 500:
        name = 'Hair'
    elif n > 150 and hi[2] < 1.01 and lo[2] > 0.9 and (hi[0] - lo[0]) > 0.15:
        name = 'Belt'
    elif hi[2] < 1.01 and lo[2] > 0.9:
        name = 'Buckle'
    else:
        name = 'Drop'                                  # eyeballs, mouth interior
    o.name = name
    parts.setdefault(name, []).append(o)
for o in parts.pop('Drop', []):
    bpy.data.objects.remove(o, do_unlink=True)
for name, objs in parts.items():                       # merge buckle fragments into one object
    if len(objs) > 1:
        for o in bpy.data.objects:
            o.select_set(o in objs)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        objs[0].name = name
parts = {o.name.split('.')[0]: o for o in bpy.data.objects if o.type == 'MESH'}
for o in parts.values():
    o.name = o.name.split('.')[0]
    for p in o.data.polygons:
        p.use_smooth = True
print('PARTS', {k: tris(o) for k, o in parts.items()})

# knee crease: relax the front of both knees
bm = bmesh.new(); bm.from_mesh(parts['Legs'].data)
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary and all(0.45 < v.co.z < 0.6 for v in e.verts)], sides=16)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
knee = [v for v in bm.verts if 0.40 < v.co.z < 0.56 and v.co.y < 0.0]
for _ in range(6):
    bmesh.ops.smooth_vert(bm, verts=knee, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.to_mesh(parts['Legs'].data); bm.free()

cover = BVHTree.FromPolygons(
    [parts[n].matrix_world @ v.co for n in ('Tunic', 'Hair') for v in parts[n].data.vertices],
    [tuple(i + (len(parts['Tunic'].data.vertices) if n == 'Hair' else 0) for i in p.vertices)
     for n in ('Tunic', 'Hair') for p in parts[n].data.polygons])


def covered(obj, v, reach=0.05):
    co_ = obj.matrix_world @ v.co
    h = cover.ray_cast(co_ + v.normal * 1e-4, v.normal, reach)
    return h[0] is not None


def decimate(obj, weight_fn, ratio):
    g = obj.vertex_groups.new(name='w')
    for v in obj.data.vertices:
        g.add([v.index], float(weight_fn(v)), 'REPLACE')
    m = obj.modifiers.new('Decimate', 'DECIMATE')
    m.ratio = ratio; m.vertex_group = 'w'; m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = obj
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.ops.object.modifier_apply(modifier=m.name)
    if 'w' in obj.vertex_groups:
        obj.vertex_groups.remove(obj.vertex_groups['w'])


head, legs = parts['Head'], parts['Legs']
decimate(head, lambda v: 1.0 if covered(head, v, 0.04) else (0.0 if v.co.y < -0.02 and v.co.z > 1.37 else 0.5), 0.80)
decimate(legs, lambda v: 1.0 if v.co.z < 0.13 or v.co.z > 0.68 else 0.45, 0.50)
bm = bmesh.new(); bm.from_mesh(legs.data)                     # weld + close the torn knee flap
knee_b = list({v for e in bm.edges if e.is_boundary for v in e.verts if 0.45 < v.co.z < 0.6})
bmesh.ops.remove_doubles(bm, verts=knee_b, dist=0.009)
edges = [e for e in bm.edges if e.is_boundary and all(0.45 < v.co.z < 0.6 for v in e.verts)]
if edges:
    bmesh.ops.holes_fill(bm, edges=edges, sides=16)
edges = [e for e in bm.edges if e.is_boundary and all(0.45 < v.co.z < 0.6 for v in e.verts)]
if edges:
    bmesh.ops.contextual_create(bm, geom=edges)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(legs.data); bm.free()
decimate(parts['Hair'], lambda v: 1.0, 0.60)
decimate(parts['Tunic'], lambda v: 1.0 if (v.co.y > 0.02 and 0.95 < v.co.z < 1.30) else 0.35, 0.82)
for side in ('ArmLeft', 'ArmRight'):
    decimate(parts[side], lambda v: 0.0 if abs(v.co.x) > 0.43 else 0.8, 0.85)   # hands keep their detail
decimate(parts['Belt'], lambda v: 1.0, 0.6)
decimate(parts['Buckle'], lambda v: 1.0, 0.22)

# skin = head + arms in one object (rig/weights treat it as the body)
for o in bpy.data.objects:
    o.select_set(o.name in ('Head', 'ArmLeft', 'ArmRight'))
bpy.context.view_layer.objects.active = parts['Head']
bpy.ops.object.join()
bpy.context.view_layer.objects.active.name = 'Body'
after = {o.name: tris(o) for o in bpy.data.objects if o.type == 'MESH'}
report = {'before': before, 'after': after, 'total_after': sum(after.values())}
json.dump(report, open(os.path.join(common.WORK, 'step1_report.json'), 'w'), indent=1)
print('STEP1', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
scene = bpy.context.scene
common.workbench_clay(scene); scene.display.shading.color_type = 'SINGLE'
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.show_wire = True
common.render_views(os.path.join(common.REVIEW, 'step1'), 0.8, 1.7, views=('front', 'three_quarter', 'left', 'back'), resolution=(500, 750))
common.render_views(os.path.join(common.REVIEW, 'step1_head'), 1.43, 0.36, views=('front', 'left'), resolution=(450, 450))
common.render_views(os.path.join(common.REVIEW, 'step1_feet'), 0.15, 0.4, views=('front', 'left'), resolution=(450, 450))
common.render_views(os.path.join(common.REVIEW, 'step1_hand'), 0.80, 0.26, views=('front',), resolution=(450, 450), target=(-0.5, 0))
