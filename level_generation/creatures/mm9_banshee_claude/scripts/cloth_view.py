"""Diagnostic: the MM9 cloth alone, studio lit, four views, bind and a pose. Args: glb out_png_prefix [action@frame]"""
import bpy, sys, math
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=A[0])
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in sc.objects:
    if o.type == 'MESH' and not o.name.startswith(sys.argv[-1] if False else 'cloth'):
        o.hide_render = o.name.startswith('Icosphere') or (A[2] == 'only')
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_backface_culling = False; sh.show_cavity = False
for o in sc.objects:
    if o.type == 'MESH':
        o.color = (1, .6, .2, 1) if o.name.startswith('cloth') else (.7, .7, .75, 1)
sc.render.resolution_x = 700; sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 2.6; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0.2, 0.1))
acts = [None] + ([A[3]] if len(A) > 3 else [])
for k, act in enumerate(acts):
    if act:
        n, f = act.split('@')
        a = bpy.data.actions.get(n) or next(x for x in bpy.data.actions if n in x.name)
        arm.animation_data_create(); arm.animation_data.action = a; sc.frame_set(int(f))
    for v, d in {'front': (0, -1, .1), 'side': (1, 0, .1), 'back': (0, 1, .1), 'top': (0, 0.1, 1), 'under': (.3, -.3, -1)}.items():
        d = Vector(d).normalized(); cam.location = c + d * 8
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{A[1]}_{k}_{v}.png'
        bpy.ops.render.render(write_still=True)
print('DONE', [a.name for a in bpy.data.actions][:20])
