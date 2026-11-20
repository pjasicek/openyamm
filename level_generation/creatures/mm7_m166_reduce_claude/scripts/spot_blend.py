"""Rest-pose textured close-ups of flagged faces (dark_slivers.py) straight from a ladder blend: source and candidates,
from outside the surface (along the face's outward direction from the head centre) and from above.
Usage: blender -b -P spot_blend.py -- <blend> <Cand_40,...> <x,y,z;...> <out dir>"""
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
objs = {'source': src, **{c.replace('Cand_', 'r'): bpy.data.objects[c] for c in args[1].split(',')}}
pts = [src.matrix_world @ Vector([float(x) for x in p.split(',')]) for p in args[2].split(';')]
out = os.path.join(HERE, args[3]); os.makedirs(out, exist_ok=True)
centre = src.matrix_world @ Vector((0, -0.067, 0.657))
cam = bpy.data.objects.new('SpotCam', bpy.data.cameras.new('SpotCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('SPOT_SIZE', '.12')); sc.render.resolution_x = sc.render.resolution_y = 300
sc.render.engine = 'BLENDER_EEVEE'; sc.render.film_transparent = False
for i, p in enumerate(pts):
    for side, d in (('out', (p - centre).normalized()), ('top', Vector((.05, .05, 1)).normalized())):
        cam.location = p + d * 2; cam.rotation_euler = (p - cam.location).to_track_quat('-Z', 'Y').to_euler()
        for label, o in objs.items():
            for q in bpy.data.objects:
                if q.type == 'MESH':
                    q.hide_render = q is not o
            sc.render.filepath = os.path.join(out, f'{label}_p{i}_{side}.png'); bpy.ops.render.render(write_still=True)
print('SPOTS', len(pts))
