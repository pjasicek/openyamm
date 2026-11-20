"""Rest-pose textured close-ups of flagged spots (flag_spots.py: 'x,y,z/nx,ny,nz;...') straight from a ladder blend:
source and candidates, along the spot's outward normal and from 45 deg beside it.
Usage: blender -b -P spot_blend.py -- <blend> <Cand_74,...> <spots> <out dir>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', args[0]))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
src = bpy.data.objects['Body']
bpy.context.view_layer.objects.active = src; src.select_set(True); bpy.ops.mesh.customdata_custom_splitnormals_clear()
objs = {'source': src, **{c.replace('Cand_', 'r'): bpy.data.objects[c] for c in args[1].split(',')}}
spots = []
for s in args[2].split(';'):
    p, n = s.split('/'); spots.append((src.matrix_world @ Vector([float(x) for x in p.split(',')]),
                                       (src.matrix_world.to_3x3() @ Vector([float(x) for x in n.split(',')])).normalized()))
out = os.path.join(HERE, args[3]); os.makedirs(out, exist_ok=True)
cam = bpy.data.objects.new('SpotCam', bpy.data.cameras.new('SpotCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('SPOT_SIZE', '.14')); cam.data.clip_end = 5
sc.render.resolution_x = sc.render.resolution_y = 300; sc.render.engine = 'BLENDER_EEVEE'; sc.render.film_transparent = False
for i, (p, n) in enumerate(spots):
    side = n.cross(Vector((0, 0, 1))); side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
    for tag, d in (('out', n), ('side', (n + side).normalized())):
        cam.location = p + d * 1.5; cam.rotation_euler = (p - cam.location).to_track_quat('-Z', 'Y').to_euler()
        for label, o in objs.items():
            for q in bpy.data.objects:
                if q.type == 'MESH':
                    q.hide_render = q is not o
            sc.render.filepath = os.path.join(out, f'{label}_p{i}_{tag}.png'); bpy.ops.render.render(write_still=True)
print('SPOTS', len(spots))
