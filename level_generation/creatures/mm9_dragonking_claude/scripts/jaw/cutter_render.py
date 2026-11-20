"""Render the MouthCutter alone (palate pink, floor orange) side/front/top/below, with the head shell as faint x-ray
context. Args: -- <blend> <out prefix>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
c = bpy.data.objects['MouthCutter']; c.hide_render = False; c.hide_set(False)
for o in bpy.data.objects:
    if o.type == 'MESH' and o != c: o.hide_render = True
c.data.materials[0].diffuse_color = (0.95, 0.5, 0.6, 1); c.data.materials[1].diffuse_color = (0.95, 0.6, 0.1, 1)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'; sc.render.resolution_x = sc.render.resolution_y = 700
sc.display.shading.show_backface_culling = False
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.9, 0.9, 0.92)
hc = Vector((0, -4.0, 15.0))
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 3.2; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for nm, d in (('side', (1, 0, 0)), ('front', (0, -1, 0)), ('top', (0, 0, 1)), ('below', (0, 0, -1)), ('q34', (0.6, -0.6, 0.4))):
    cam.location = hc + Vector(d).normalized() * 10
    cam.rotation_euler = (hc - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{nm}.png'; bpy.ops.render.render(write_still=True)
