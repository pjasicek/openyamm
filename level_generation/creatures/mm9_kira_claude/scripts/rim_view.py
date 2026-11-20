"""Rest-pose views of one wrist with the glove hidden or shown (analysis for wrist_fill.py). Args: <blend> <out prefix> <side> [hide_hand 1]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, S = a[:3]; HIDE = (a[3] if len(a) > 3 else '1') == '1'
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
for m in list(body.modifiers): body.modifiers.remove(m)
bm = bmesh.new(); bm.from_mesh(me); lk = bm.faces.layers.int['hand']; lp = bm.faces.layers.int['part']
if HIDE: bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lk]], context='FACES')
bm.to_mesh(me); bm.free()
fa = rig.matrix_world @ rig.data.bones[f'Bip01 {S} Forearm'].head_local; hd = rig.matrix_world @ rig.data.bones[f'Bip01 {S} Hand'].head_local
f = (hd - fa).normalized(); o = Vector((hd.x, 0, 0)).normalized(); o = (o - f * o.dot(f)).normalized(); b = f.cross(o)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'
sh.single_color = (.72, .7, .62); sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 420
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.5, 0.05, 0.4); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'; cd.ortho_scale = float(__import__('os').environ.get('ORTHO', 0.12)); cd.clip_end = 30
for name, d in (('axis', f + 0.15 * o), ('above', -f + 0.6 * o), ('aboveb', -f + 0.6 * b), ('abovef', -f - 0.6 * b), ('side', o + 0.2 * f)):
    d = d.normalized(); cam.location = hd + d * 3; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{OUT}_{name}.png'; bpy.ops.render.render(write_still=True)
print('RIMVIEW done')
