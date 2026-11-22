"""Render one clip frame of a creature GLB from front / three-quarter / side / back (workbench, textured).
Usage: blender -b --python pose_views.py -- <src.glb> <out.png> <action> <frame> [size]"""
import math, os, sys
import bpy
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, out, action, frame = argv[0], argv[1], argv[2], float(argv[3])
size_px = int(argv[4]) if len(argv) > 4 else 500
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
arm = next((o for o in sc.objects if o.type == 'ARMATURE'), None)
meshes = [o for o in sc.objects if o.type == 'MESH' and (arm is None or o.find_armature() is arm or o.parent is not None or len(sc.objects) < 4)]
for o in sc.objects:
    if o.type == 'MESH' and o not in meshes: o.hide_render = True
for o in meshes:
    if 'Shadow' in o.name or 'LOD' in o.name:
        o.hide_render = True
if arm is not None and action == '-':
    if arm.animation_data: arm.animation_data.action = None
    for pb in arm.pose.bones: pb.matrix_basis.identity()
if arm is not None and action != '-':
    if arm.animation_data is None:
        arm.animation_data_create()
    act = bpy.data.actions[action]
    arm.animation_data.action = act
    if hasattr(arm.animation_data, 'action_slot') and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
sc.frame_set(int(frame))
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'TEXTURE'
sc.display.shading.show_cavity = True
sc.render.resolution_x = size_px
sc.render.resolution_y = int(size_px * 1.3)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dg = bpy.context.evaluated_depsgraph_get()
lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
for o in meshes:
    if o.hide_render: continue
    ev = o.evaluated_get(dg); me = ev.to_mesh()
    for v in me.vertices:
        w = ev.matrix_world @ v.co; lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    ev.to_mesh_clear()
c = (lo + hi) / 2; s = max(hi - lo)
import os as _os
if _os.environ.get('VIEW_BOX'):
    bx = [float(x) for x in _os.environ['VIEW_BOX'].split(',')]
    c = Vector(bx[:3]); s = bx[3]
print('BOUNDS', tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
tiles = []
fwd = argv[5] if len(argv) > 5 else '-Y'
for name, az in (('front', 0), ('q', 35), ('side', 90), ('back', 180)):
    a = math.radians(az)
    d0 = Vector((0, -1, 0)) if fwd == '-Y' else Vector((0, 1, 0)) if fwd == '+Y' else Vector((1, 0, 0)) if fwd == '+X' else Vector((-1, 0, 0))
    d = Vector((d0.x * math.cos(a) - d0.y * math.sin(a), d0.x * math.sin(a) + d0.y * math.cos(a), 0.12)).normalized()
    cam.location = c + d * s * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.ortho_scale = s * 1.1
    p = out.replace('.png', f'_{name}.png'); sc.render.filepath = p
    bpy.ops.render.render(write_still=True); tiles.append(p)
import subprocess
subprocess.run(['/usr/bin/python3', '-c', 'import sys;from PIL import Image\nims=[Image.open(p) for p in sys.argv[2:]]\ns=Image.new("RGB",(sum(i.width for i in ims),ims[0].height))\nx=0\nfor i in ims: s.paste(i,(x,0)); x+=i.width\ns.save(sys.argv[1])\nimport os\n[os.remove(p) for p in sys.argv[2:]]', out] + tiles, check=True)
print('DONE', out)
