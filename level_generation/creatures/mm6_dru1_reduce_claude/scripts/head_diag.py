"""Forehead/hood diagnosis of a viewer GLB (Standing frame 0): textured EEVEE render plus a Workbench render with one
flat colour per part, classified per face from the atlas at the UV centroid (skin face, hair brown, hood = region-mask
cloth, other) and back faces (normal away from the camera) in red. Usage: blender -b -P head_diag.py -- <glb> <label>"""
import os, sys, math, bpy, bmesh
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.data.uv_layers and not o.hide_render and 'LOD' not in o.name and 'Shadow' not in o.name)
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body: o.hide_render = True
head = next(b for b in rig.pose.bones if b.name.endswith('Head'))
c = rig.matrix_world @ head.head + Vector((0, 0, .07))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('DIAG_SIZE', '.32'))
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 700
views = {'front': Vector((0, -1, .05)), 'low': Vector((0, -1, -.35)), 'q34': Vector((.6, -.8, .05))}
def shoot(tag):
    for v, d in views.items():
        dv = d.normalized(); cam.location = c + dv * 3
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(HERE, 'review/head', f'{label}_{tag}_{v}.png'); bpy.ops.render.render(write_still=True)
sc.render.engine = 'BLENDER_EEVEE'; shoot('tex')
# classify faces from the base colour + region mask images of the material
mat = body.data.materials[0]
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
base = bsdf.inputs['Base Color'].links[0].from_node.image
def arr(im):
    a = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], im.channels); return a
B = arr(base); H, W = B.shape[:2]
me = body.data; uv = me.uv_layers.active.data
cls = []
for p in me.polygons:
    u = sum(uv[l].uv[0] for l in p.loop_indices) / p.loop_total; v = sum(uv[l].uv[1] for l in p.loop_indices) / p.loop_total
    x = min(W - 1, max(0, int(u * W))); y = min(H - 1, max(0, int(v * H)))   # Blender pixels: row 0 = bottom
    r, g, b = B[y, x, :3]
    head_set = u > .5
    if not head_set: cls.append(4)
    elif g > r * 1.1 or (g > b * 1.3 and g > r * .95): cls.append(2)          # hood green
    elif r > .5 and g > r * .55 and b > r * .35: cls.append(0)               # skin
    else: cls.append(1)                                                       # hair / dark
cols = [(0.95, .7, .55, 1), (.45, .25, .1, 1), (.1, .7, .2, 1), (.9, .9, .2, 1), (.3, .4, .9, 1)]
me.materials.clear()
for i, col in enumerate(cols):
    m = bpy.data.materials.new(f'C{i}'); m.diffuse_color = col; me.materials.append(m)
for p, k in zip(me.polygons, cls): p.material_index = k
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_backface_culling = True
shoot('parts_cull')
sh.show_backface_culling = False; shoot('parts')
print('CLASSES', {k: cls.count(k) for k in range(5)})
