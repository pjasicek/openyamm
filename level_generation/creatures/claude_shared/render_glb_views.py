"""Render a creature GLB in its rest pose: front and side orthographic views under one sun from above-front and a
grey sky (Eevee), for before/after texture comparisons. The materials' own base colour textures are used (region
ramps are not applied: regions without a ramp, and tier A of shared skins, render as in game).
Usage: blender --background --python render_glb_views.py -- <in.glb> <out_prefix> [front_axis -y|+y] [size]
       [image_substring=override.png ...]   (replace images whose name contains the substring, e.g. a tier
       texture from tier_textures.py, so the render shows that tier)
Writes <out_prefix>_front.png and <out_prefix>_side.png."""
import bpy, sys, math
import numpy as np
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[0], args[1]; front = -1.0 if (len(args) < 3 or args[2] == '-y') else 1.0
size = int(args[3]) if len(args) > 3 else 600
overrides = dict(a.split('=', 1) for a in args[4:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for arm in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
    if arm.animation_data:
        arm.animation_data.action = None
    for b in arm.pose.bones:
        b.matrix_basis.identity()
loaded = {}
for mat in bpy.data.materials:
    if not mat.node_tree:
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            for key, path in overrides.items():
                if key in node.image.name:
                    if path not in loaded:
                        loaded[path] = bpy.data.images.load(path)
                    node.image = loaded[path]
bpy.context.view_layer.update()
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and 'Shadow' not in o.name and 'LOD' not in o.name
          and 'Shadow' not in o.data.name and 'LOD' not in o.data.name]
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in meshes:
        o.hide_render = True
dg = bpy.context.evaluated_depsgraph_get()
co = np.concatenate([np.array([tuple(o.matrix_world @ v.co) for v in o.evaluated_get(dg).data.vertices]) for o in meshes])
lo, hi = np.percentile(co, 0.2, axis=0), np.percentile(co, 99.8, axis=0)
c = Vector((lo + hi) / 2); ext = float((hi - lo).max())
print('MESHES', [o.name for o in meshes], 'extent', np.round(hi - lo, 3))
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.45, 0.47, 0.52, 1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.8
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(40), 0, math.radians(200 if front < 0 else 20))
sc.render.resolution_x = sc.render.resolution_y = size; sc.render.film_transparent = False
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = ext * 1.05
for name, d in (('front', Vector((0, -front, -0.12))), ('side', Vector((1, 0, -0.12)))):
    d.normalize(); cam.location = c - d * ext * 4; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{name}.png'; bpy.ops.render.render(write_still=True)
print('RENDERED', out)
