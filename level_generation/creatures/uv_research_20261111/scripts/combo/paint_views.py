"""Identical-camera views of one paint on one layout (combined-layout study, paint evaluation).

Opens a seam-trial / apply_layout blend (the prepared mesh of one texture set, bind pose), puts <image> on it as an
unlit texture (Workbench, FLAT light, linear filtering with GPU mipmaps, as the runtime samples a 2K map), and renders
the views of a JSON spec. Cameras are computed from the mesh's bind-pose geometry only (vertex-group centroids), so
every layout and paint of the same set gets exactly the same cameras.

run_creature_blender.sh .../paint_views.py <blend> <image png> <spec json> <out dir> <label>
spec: {"front_az": deg, "views": [{"name", "groups": [prefix, ...] | [], "az": deg (from front), "el": deg,
        "fill": share of the frame height the target spans, "res": px, "lens": mm}]}
Writes <out dir>/<label>_<view>.png (RGBA: alpha is the mesh coverage).
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
BLEND, IMAGE, SPEC, OUT, LABEL = argv[:5]
spec = json.load(open(SPEC))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if rig is not None:
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
mesh = max(meshes, key=lambda o: len(o.data.polygons))
for o in meshes:
    if o != mesh:
        bpy.data.objects.remove(o)
for o in list(bpy.data.objects):
    if o.type not in ('MESH', 'ARMATURE'):
        bpy.data.objects.remove(o)
bpy.context.view_layer.update()
img = bpy.data.images.load(IMAGE)
mat = bpy.data.materials.new('paint')
mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = img
tex.interpolation = 'Linear'
mat.node_tree.links.new(tex.outputs[0], bsdf.inputs[0])
me = mesh.data
me.materials.clear()
me.materials.append(mat)
for p in me.polygons:
    p.material_index = 0
uvname = 'UVMap' if 'UVMap' in me.uv_layers else me.uv_layers[0].name
me.uv_layers.active = me.uv_layers[uvname]
me.uv_layers[uvname].active_render = True

dg = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(dg)
mw = mesh.matrix_world
pts = np.array([tuple(mw @ v.co) for v in ev.data.vertices])
names = [g.name for g in mesh.vertex_groups]
weight = np.zeros((len(me.vertices), len(names)), np.float32)
for v in me.vertices:
    for g in v.groups:
        weight[v.index, g.group] = g.weight

scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    scene.render.engine = 'WORKBENCH'
scene.display.shading.light = 'FLAT'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_cavity = False
scene.display.shading.show_shadows = False
scene.display.render_aa = '8'
scene.view_settings.view_transform = 'Standard'
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
cam_data = bpy.data.cameras.new('cam')
cam = bpy.data.objects.new('cam', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
front = spec.get('front_az', 0)
for view in spec['views']:
    groups = [i for i, n in enumerate(names) if any(n.startswith(p) for p in view.get('groups', []))]
    sel = (weight[:, groups].sum(1) >= 0.5) if groups else np.ones(len(pts), bool)
    if not sel.any():
        raise ValueError(f"no vertices for view {view['name']}")
    target = pts[sel]
    centre = Vector(tuple((target.min(0) + target.max(0)) / 2))
    radius = float(np.linalg.norm(target.max(0) - target.min(0))) / 2
    a, e = math.radians(front + view.get('az', 0)), math.radians(view.get('el', 8))
    d = Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
    cam_data.lens = view.get('lens', 50)
    cam_data.sensor_fit = 'VERTICAL'
    half = math.atan(cam_data.sensor_height / 2 / cam_data.lens)
    dist = radius / view.get('fill', 0.9) / math.tan(half)
    cam_data.clip_start, cam_data.clip_end = dist * 0.01, dist * 10
    cam.location = centre + d * dist
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x = scene.render.resolution_y = view.get('res', 640)
    scene.render.filepath = os.path.join(OUT, f"{LABEL}_{view['name']}.png")
    bpy.ops.render.render(write_still=True)
print('VIEWS done', LABEL, flush=True)
