"""Close renders of the knife collar, pommel and blade tip, textured and clay: review/props/close_<tag>_<shot>.png.
Usage: blender -b -P knife_close.py -- <glb> <tag>"""
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
# world space after import: the knife lies along y (collar -0.06, pommel +0.045, blade to -0.23), 18 mm thick in z
T = {'collar': Vector((0.005, -0.06, 0)), 'pommel': Vector((0.005, 0.04, 0)), 'tip': Vector((0.015, -0.19, 0))}
shots = {k: (t + Vector((.07, -.03, .09)), t) for k, t in T.items()}
for engine in ('EEVEE', 'WORKBENCH'):
    try: sc.render.engine = 'BLENDER_' + engine + ('_NEXT' if engine == 'EEVEE' else '')
    except TypeError: sc.render.engine = 'BLENDER_' + engine
    if engine == 'WORKBENCH':
        sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_cavity = True
    for k, (p, t) in shots.items():
        cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(HERE, 'review/props', f'close_{tag}_{k}{"_clay" if engine == "WORKBENCH" else ""}.png')
        bpy.ops.render.render(write_still=True)
