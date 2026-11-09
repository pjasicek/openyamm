"""Textured rest-pose close-ups (Standing frame 0) of the source and ladder candidates around given points, viewed
along the outward direction from the body axis (for dark-sliver and drift spots). Usage:
blender -b -P point_close.py -- <blend> <Cand_82,...> <name=x,y,z;...> [size] -> review/close/<label>_<name>_tex.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
objs = {'source': bpy.data.objects['Body'], **{c.replace('Cand_', 'r'): bpy.data.objects[c] for c in a[1].split(',')}}
size = float(a[3]) if len(a) > 3 else .25
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
if cam.name not in sc.collection.objects:
    sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = size; cam.data.clip_end = 10
sc.render.resolution_x = sc.render.resolution_y = 360; sc.render.engine = 'BLENDER_EEVEE'
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = True
for item in a[2].split(';'):
    name, xyz = item.split('='); p = Vector([float(t) for t in xyz.split(',')])
    dv = Vector((p.x, p.y, 0)); dv = dv.normalized() if dv.length > 1e-3 else Vector((0, -1, 0))
    cam.location = p + dv * 3; cam.rotation_euler = (p - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for label, o in objs.items():
        for q in objs.values():
            q.hide_render = q is not o
        sc.render.filepath = os.path.join(HERE, 'review', 'close', f'{label}_{name}_tex.png'); bpy.ops.render.render(write_still=True)
print('POINTCLOSE done')
