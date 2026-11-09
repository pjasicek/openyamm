"""Render the front-detail face groups (work/detail_faces.json) in colour on the clay model, front / three-quarter /
side -> review/detail_faces.png. Usage: blender -b -P detail_faces_view.py"""
import json, math, os, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_body.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
o = bpy.data.objects['Cand_62']; o.hide_render = False
for x in bpy.data.objects:
    if x.type == 'MESH' and x is not o:
        x.hide_render = True
groups = json.load(open(os.path.join(HERE, 'work', 'detail_faces.json')))
cols = {'none': (.6, .6, .6), 'collar_neck': (1, .5, 0), 'capelet': (.1, .8, .2), 'chest': (.9, .1, .2), 'tabard': (.8, .2, .9), 'belt_clasp': (1, .9, .1)}
o.data.materials.clear()
for name, c in cols.items():
    m = bpy.data.materials.new(name); m.diffuse_color = (*c, 1); o.data.materials.append(m)
names = list(cols)
for p in o.data.polygons:
    p.material_index = 0
for g, faces in groups.items():
    for fi in faces:
        o.data.polygons[fi].material_index = names.index(g)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.light = 'STUDIO'; sc.render.resolution_x = sc.render.resolution_y = 500
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
cam.data.ortho_scale = 1.1; target = Vector((0, 0, 1.15)); shots = []
for i, d in enumerate([(0, -1, .1), (.7, -.7, .25), (1, 0, .1)]):
    cam.location = target + Vector(d).normalized() * 4; cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    path = os.path.join(HERE, 'review', f'detail_faces_{i}.png'); sc.render.filepath = path; bpy.ops.render.render(write_still=True); shots.append(path)
print('SHOTS', shots)
