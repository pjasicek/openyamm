"""Close renders of the mace head and grip, textured and clay: review/props/close_<tag>_<shot>.png.
Usage: blender -b -P mace_close.py -- <glb> <tag>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, tag = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
for o in bpy.data.objects:
    if o.type == 'MESH' and 'LOD' in o.name: o.hide_render = True
sc = bpy.context.scene; sc.render.resolution_x = sc.render.resolution_y = 500
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[0].default_value = (0.55, 0.6, 0.66, 1)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (0.8, 0.3, 0.6)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
mace = next(o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render)
M = mace.matrix_world
head, grip = M @ Vector((0, 0, .385)), M @ Vector((0, 0, 0))
shots = {'head': (head + (M.to_3x3() @ Vector((.25, -.25, .08))), head), 'grip': (grip + (M.to_3x3() @ Vector((.15, -.15, .1))), grip + (M.to_3x3() @ Vector((0, 0, .05))))}
for engine in ('EEVEE', 'WORKBENCH'):
    try: sc.render.engine = 'BLENDER_' + engine + ('_NEXT' if engine == 'EEVEE' else '')
    except TypeError: sc.render.engine = 'BLENDER_' + engine
    if engine == 'WORKBENCH':
        sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_cavity = True
    for k, (p, t) in shots.items():
        cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(HERE, 'review/props', f'close_{tag}_{k}{"_clay" if engine == "WORKBENCH" else ""}.png')
        bpy.ops.render.render(write_still=True)
