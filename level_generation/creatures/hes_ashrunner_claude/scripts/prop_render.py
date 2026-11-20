"""Textured EEVEE renders of the blaster prop (work/blaster.blend) from both sides and three-quarter -> review/blaster_*.png.
Args: none"""
import bpy, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'blaster.blend'))
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 640, 400
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[1].default_value = 1.5
sun = bpy.data.objects.new('s', bpy.data.lights.new('s', 'SUN')); sc.collection.objects.link(sun); sun.rotation_euler = (0.6, 0.3, 0.8)
for name, pos in (('right', (0.6, 0.12, 0.03)), ('left', (-0.6, 0.12, 0.03)), ('tq', (0.4, 0.5, 0.25))):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(cam); cam.data.lens = 50
    cam.location = pos; cam.rotation_euler = (Vector((0, 0.12, 0.03)) - Vector(pos)).to_track_quat('-Z', 'Z').to_euler()
    sc.camera = cam; sc.render.filepath = os.path.join(HERE, 'review', f'blaster_{name}.png'); bpy.ops.render.render(write_still=True)
