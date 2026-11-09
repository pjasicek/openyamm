"""Debug render of a graft blend: body grey, head faces red, bridge faces green, no hair (kind 3 verts hidden).
Args: -- <blend> <out png prefix> [scale]"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me)
kl = bm.verts.layers.int.get('kind')
if kl and os.environ.get('NOHAIR', '1') == '1':
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[kl] == 3], context='VERTS')
hl = bm.faces.layers.int.get('head'); br = bm.faces.layers.int.get('bridge')
for f in bm.faces:
    f.material_index = (2 if br and f[br] else (1 if hl and f[hl] else 0))
bm.to_mesh(me)
me.materials.clear()
for c in ((0.7, 0.7, 0.72, 1), (0.85, 0.4, 0.35, 1), (0.3, 0.8, 0.35, 1)):
    m = bpy.data.materials.new('m'); m.diffuse_color = c; me.materials.append(m)
for mm in list(body.modifiers):
    body.modifiers.remove(mm)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 600
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.32, 0.33, 0.36)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[2]) if len(a) > 2 else 0.6
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, -0.12, 1.42))
for nm, d in (('front', (0, -1, 0)), ('side', (-1, 0, 0)), ('back', (0, 1, 0)), ('q34', (-0.8, -1, 0.3))):
    dv = Vector(d).normalized(); cam.location = c + dv * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{nm}.png'; bpy.ops.render.render(write_still=True)
