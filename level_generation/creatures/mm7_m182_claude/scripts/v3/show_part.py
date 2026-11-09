"""Render only the faces of Body whose vertices all satisfy a numpy mask file (bool per vertex), plus a translucent
rest. Usage: blender -b <blend> -P show_part.py -- <mask.npy> <out.png> <view dir x,y,z> <target x,y,z> <scale>"""
import bpy, bmesh, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
mask = np.load(a[0]); body = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(mask[v.index] for v in f.verts)], context='FACES')
bm.to_mesh(body.data); bm.free()
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body: o.hide_render = True
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'TEXTURE'; sc.render.resolution_x = sc.render.resolution_y = 800
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
d = Vector([float(v) for v in a[2].split(',')]); t = Vector([float(v) for v in a[3].split(',')])
cam.location = t + d.normalized() * 10; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = float(a[4])
rig = bpy.data.objects.get('Rig')
if rig and rig.animation_data: rig.animation_data.action = None
if rig:
    for b in rig.pose.bones: b.matrix_basis.identity()
sc.render.filepath = a[1]; bpy.ops.render.render(write_still=True)
