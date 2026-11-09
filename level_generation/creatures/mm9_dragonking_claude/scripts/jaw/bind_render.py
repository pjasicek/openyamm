"""Bind-pose snout renders of a work blend: shell grey, palate pink, floor orange, teeth yellow (tooth attr),
solid and x-ray; optional cutter wireframe. Args: -- <blend> <out prefix>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
body = bpy.data.objects['Body']; me = body.data
rig = bpy.data.objects['MM9_Rig']
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH' and o != body: o.hide_render = True
me.materials.clear()
for c in ((0.6, 0.6, 0.6, 1), (0.95, 0.5, 0.6, 1), (0.95, 0.6, 0.1, 1), (1, 0.95, 0.3, 1), (0.3, 0.9, 0.3, 1)):
    m = bpy.data.materials.new('m'); m.diffuse_color = c; me.materials.append(m)
mo = me.attributes.get('mouth'); to = me.attributes.get('tooth'); stv = me.attributes.get('stray')
for p in me.polygons:
    k = mo.data[p.index].value if mo else 0
    t = to.data[p.index].value if to else 0
    p.material_index = k if k else (3 if t == 1 else 4 if t == 2 else 0)
    if stv and stv.data[p.index].value: p.material_index = 4
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'; sc.render.resolution_x = sc.render.resolution_y = 700
sc.display.shading.show_backface_culling = False
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.9, 0.9, 0.92)
hc = Vector((0, -4.0, 15.05))
cd = bpy.data.cameras.new('c'); cd.lens = 85; cd.clip_start = 0.01; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for xr in (False, True):
    sc.display.shading.show_xray = xr; sc.display.shading.xray_alpha = 0.35
    for nm, d in (('side', (1, -0.1, 0.05)), ('frontlow', (0.35, -1, -0.3)), ('below', (0.1, -0.15, -1))):
        cam.location = hc + Vector(d).normalized() * 5.5
        cam.rotation_euler = (hc - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{out}_{nm}_{int(xr)}.png'; bpy.ops.render.render(write_still=True)
