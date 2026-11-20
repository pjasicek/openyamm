"""Exact orthographic renders of the painted head (the woman) for the Codex skull repaint: flat unlit texture, transparent background. Because they are ours, the repaint projects back with known cameras, no landmarks.
Args: <uv blend> <head png> <out dir>"""
import bpy, sys, os
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=A[0])
sc = bpy.context.scene
head = bpy.data.objects['Head']
for o in sc.objects:
    if o.type == 'MESH' and o is not head:
        o.hide_render = True
for m in list(head.modifiers):
    head.modifiers.remove(m)
mat = bpy.data.materials.new('h'); mat.use_nodes = True
nt = mat.node_tree
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(A[1])
b = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED')
nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
head.data.materials.clear(); head.data.materials.append(mat)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = True
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.render.resolution_x = 1024; sc.render.resolution_y = 1024
ORTHO, C = 0.46, Vector((0, -0.235, 0.60))
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ORTHO; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
os.makedirs(A[2], exist_ok=True)
for n, d in {'01_front': (0, -1, 0), '02_back': (0, 1, 0), '03_left': (-1, 0, 0), '04_right': (1, 0, 0)}.items():
    d = Vector(d); cam.location = C + d * 5
    cam.rotation_euler = (C - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(A[2], n + '.png'); bpy.ops.render.render(write_still=True)
print('VIEWS')
