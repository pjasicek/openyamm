"""Raw Meshy return (meshy/bat_texture_r1/model_urls_glb.glb) rendered as is: front, head close-up, side."""
import os, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/bat_texture_r1/model_urls_glb.glb'))
ob = next(o for o in bpy.data.objects if o.type == 'MESH')
bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]; lo = Vector([min(p[k] for p in bb) for k in range(3)]); hi = Vector([max(p[k] for p in bb) for k in range(3)])
print('BOUNDS', tuple(lo), tuple(hi))
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 800
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .5, .55, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.5
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
c = (lo + hi) / 2; size = (hi - lo).length
os.makedirs(os.path.join(HERE, 'review', 'meshy'), exist_ok=True)
for name, d, sz, cc in [('front', (0, 1, 0), .8, c), ('back', (0, -1, 0), .8, c)]:
    cam.location = cc + Vector(d) * 5; cam.rotation_euler = (cc - cam.location).to_track_quat('-Z', 'Z').to_euler(); cam.data.ortho_scale = size * sz
    sc.render.filepath = os.path.join(HERE, 'review', 'meshy', f'raw_{name}.png'); bpy.ops.render.render(write_still=True)
