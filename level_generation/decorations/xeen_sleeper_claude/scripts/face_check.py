"""Face close-up of the laid body (work/body.blend) with a base colour (workbench, flat texture).
Usage: blender -b --python face_check.py -- <basecolor.png> <out.png> [lod]"""
import os, sys
import bpy
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
here = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(here, '..', 'work', 'body.blend'))
lod = int(argv[2]) if len(argv) > 2 else 0
ob = bpy.data.objects[f'Body_LOD{lod}']
for o in bpy.context.scene.objects:
    o.hide_render = o is not ob
mat = bpy.data.materials.new('m'); mat.use_nodes = True
t = mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.abspath(argv[0]))
b = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
mat.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
ob.data.materials.clear(); ob.data.materials.append(mat)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.render.resolution_x, scene.render.resolution_y = 700, 500
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam); scene.camera = cam
co = [ob.matrix_world @ v.co for v in ob.data.vertices]
import json
info = json.load(open(os.path.join(here, '..', 'work', 'body.json')))
target = Vector(info['eye_centre'])
cam.data.lens = 50
eye = target + Vector(info["eye_normal"]) * float(argv[3] if len(argv) > 3 else 1.4) + Vector((0.3, -0.3, 0.0))
cam.location = eye; cam.rotation_euler = (target - eye).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = os.path.abspath(argv[1]); bpy.ops.render.render(write_still=True)
