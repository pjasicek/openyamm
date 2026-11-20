"""Exact-body guide renders for the HD masters: the winged Kreegan body in its rest pose, wings hidden (Meshy and
Codex get only the body to armour), transparent background. Orthographic front/back/left/right and a perspective
front-left three-quarter; the camera of every view is written to <out_dir>/cameras.json for later projection.

Usage (Blender): render_guides.py <body.glb> <out_dir> [size]"""
import bpy, sys, math, json
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
src, out = args[0], args[1]
size = int(args[2]) if len(args) > 2 else 1024
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == 'ARMATURE')
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
body = bpy.data.objects['OV_Assembled']
for o in sc.objects:
    if o.type == 'MESH' and o != body:
        o.hide_render = True
# Hide the wings: faces whose vertices are mostly weighted to wing bones other than the root.
wing = {g.index for g in body.vertex_groups if g.name.startswith('B_Wing_')}
me = body.data
wv = np.zeros(len(me.vertices))
for v in me.vertices:
    wv[v.index] = sum(g.weight for g in v.groups if g.group in wing)
# Islands: a mostly wing-weighted island (membrane, wing arms, wing claws) is hidden whole.
parent = list(range(len(me.vertices)))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for e in me.edges:
    a_, b_ = find(e.vertices[0]), find(e.vertices[1])
    if a_ != b_:
        parent[a_] = b_
roots = np.array([find(i) for i in range(len(me.vertices))])
hidden = np.zeros(len(me.vertices), bool)
for r in np.unique(roots):
    sel = roots == r
    if wv[sel].mean() > 0.3:
        hidden[sel] = True
hidden |= wv > 0.25
# Wing-arm spurs above the shoulders are weighted to the spine: drop islands floating above the shoulders that
# carry no head weight.
head = {g.index for g in body.vertex_groups if g.name in ('B_Head', 'B_Neck')}
hv = np.array([sum(g.weight for g in v.groups if g.group in head) for v in me.vertices])
pos = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
for r in np.unique(roots):
    sel = roots == r
    if pos[sel, 2].mean() > 1.38 and hv[sel].mean() < 0.2 and sel.sum() < 400:
        hidden[sel] = True
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[int(i)] for i in np.nonzero(hidden)[0]], context='VERTS')
bm.to_mesh(me); bm.free()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg).data
co = np.array([tuple(body.matrix_world @ v.co) for v in ev.vertices])
lo, hi = co.min(0), co.max(0)
c = Vector((lo + hi) / 2)
print('BODY BOX', lo.round(3), hi.round(3))
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.5, 0.5, 0.52, 1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
sc.render.resolution_x = size; sc.render.resolution_y = size * 3 // 2
sc.render.film_transparent = True
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 2.4
sc.collection.objects.link(sun); sun.rotation_euler = (math.radians(40), 0, math.radians(-25))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
height = float(hi[2] - lo[2])
views = {'01_front': Vector((0, -1, 0)), '02_back': Vector((0, 1, 0)),
         '03_left': Vector((1, 0, 0)), '04_right': Vector((-1, 0, 0)),
         '00_three_quarter': Vector((0.62, -0.78, 0.0))}
cams = {}
for name, d in views.items():
    d = d.normalized()
    if name == '00_three_quarter':
        cam.data.type = 'PERSP'; cam.data.lens = 50; cam.data.sensor_width = 36; cam.data.sensor_fit = 'VERTICAL'
        cam.location = c + d * height * 3.0
    else:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = height * 1.25
        cam.location = c + d * height * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.clip_end = 100
    bpy.context.view_layer.update()
    sc.render.filepath = f'{out}/{name}.png'
    bpy.ops.render.render(write_still=True)
    proj = cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(), x=sc.render.resolution_x,
                                  y=sc.render.resolution_y) @ cam.matrix_world.inverted()
    cams[name] = {'projection': [list(r) for r in proj],'type': cam.data.type, 'matrix_world': [list(r) for r in cam.matrix_world],
                  'ortho_scale': cam.data.ortho_scale, 'lens': cam.data.lens, 'sensor_width': cam.data.sensor_width,
                  'size': [size, size * 3 // 2], 'sensor_fit': cam.data.sensor_fit}
json.dump({'cameras': cams, 'body_box': [lo.tolist(), hi.tolist()]}, open(f'{out}/cameras.json', 'w'), indent=1)
print('GUIDES DONE')
