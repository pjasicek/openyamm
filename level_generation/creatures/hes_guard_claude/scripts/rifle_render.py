"""Textured EEVEE renders of the rifle prop (work/rifle.blend) from both sides and three-quarter -> review/blaster_*.png.
Args: none"""
import bpy, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rifle.blend'))
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1100, 420
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[1].default_value = 1.5
sun = bpy.data.objects.new('s', bpy.data.lights.new('s', 'SUN')); sc.collection.objects.link(sun); sun.rotation_euler = (0.6, 0.3, 0.8)
for name, pos in (('right', (1.9, 0.27, 0.03)), ('left', (-1.9, 0.27, 0.03)), ('tq', (1.2, 1.3, 0.6))):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(cam); cam.data.lens = 45
    cam.location = pos; cam.rotation_euler = (Vector((0, 0.27, 0.03)) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam; sc.render.filepath = os.path.join(HERE, 'review', f'rifle_{name}.png'); bpy.ops.render.render(write_still=True)
