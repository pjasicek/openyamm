"""Whole-model views of a viewer GLB (Standing frame 0) framed on its bounds: front, three-quarter, side, top.
Usage: blender -b -P whole_views.py -- <glb> <label> <out dir>"""
import os, sys, math, bpy
from mathutils import Vector
glb, label, out = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions.get('Standing')
if act: rig.animation_data.action = act
sc.frame_set(0)
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
dg = bpy.context.evaluated_depsgraph_get(); pts = []
for o in meshes:
    e = o.evaluated_get(dg); m = e.to_mesh(); pts += [o.matrix_world @ v.co for v in m.vertices]; e.to_mesh_clear()
lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
c = (lo + hi) / 2; size = (hi - lo).length
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * .9
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.36, .36, .4, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 520
os.makedirs(out, exist_ok=True)
for view, d in {'front': (0, -1, .15), 'q34': (.7, -.7, .35), 'side': (1, 0, .1), 'top': (.05, -.1, 1)}.items():
    dv = Vector(d).normalized(); cam.location = c + dv * size * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{label}_{view}.png'); bpy.ops.render.render(write_still=True)
