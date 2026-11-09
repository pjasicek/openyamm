"""Render the interior-face classification (interior red, teeth yellow, eyes magenta, tongue blue). Args: -- <blend> <out>"""
import bpy, sys, os, bmesh
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mouth_common as M
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
body = bpy.data.objects['Body']; me = body.data
for o in bpy.data.objects:
    if o.type == 'MESH' and o != body: o.hide_render = True
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
comp = M.parts(bm); R = M.roles(bm, comp)
inside = M.interior_faces(bm, comp, R['shell'])
print('ROLES', {k: v for k, v in R.items()}, 'interior', len(inside))
me.materials.clear()
for c in ((0.6, 0.6, 0.6, 1), (0.9, 0.1, 0.1, 1), (1, 0.85, 0.2, 1), (0.9, 0.1, 0.9, 1), (0.1, 0.3, 1, 1)):
    m = bpy.data.materials.new('m'); m.diffuse_color = c; me.materials.append(m)
for f in bm.faces:
    k = comp[f.verts[0].index]
    f.material_index = 1 if f.index in inside else 2 if k in R['teeth'] else 3 if k in R['eyes'] else 4 if k == R['tongue'] else 0
bm.to_mesh(me)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'; sc.render.resolution_x = sc.render.resolution_y = 700
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.9, 0.9, 0.92)
hc = Vector((0, -4.2, 15.1))
cd = bpy.data.cameras.new('c'); cd.lens = 85; cd.clip_start = 0.01; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for xr in (False, True):
    sc.display.shading.show_xray = xr; sc.display.shading.xray_alpha = 0.3
    for nm, d in (('side', (1, -0.1, 0.05)), ('frontlow', (0.35, -1, -0.3)), ('below', (0.1, -0.15, -1))):
        cam.location = hc + Vector(d).normalized() * 5
        cam.rotation_euler = (hc - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{out}_{nm}_{int(xr)}.png'; bpy.ops.render.render(write_still=True)
