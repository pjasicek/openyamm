"""Clay close-ups of the source Body and a candidate at one rest-pose spot (mesh-local coordinates of mesh_in.npz),
from several directions, for diagnosis. Usage: blender -b -P view_spot.py -- <ladder blend> <Cand_NN> <x,y,z> <radius m> <out prefix>"""
import sys, math, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
src = bpy.data.objects['Body']; cand = bpy.data.objects[a[1]]
p = src.matrix_world @ Vector([float(x) for x in a[2].split(',')]); R = float(a[3])
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'SINGLE'; sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 420
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2 * R
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = True
dirs = {'x': (1, 0, 0), 'y': (0, -1, 0), 'z': (0, 0, 1), 'q': (0.6, -0.6, 0.5)}
for name, obj in (('src', src), ('cand', cand)):
    for o in (src, cand):
        o.hide_render = o is not obj
    for dn, d in dirs.items():
        dv = Vector(d).normalized(); cam.location = p + dv * 3
        cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{a[4]}_{dn}_{name}.png'; bpy.ops.render.render(write_still=True)
