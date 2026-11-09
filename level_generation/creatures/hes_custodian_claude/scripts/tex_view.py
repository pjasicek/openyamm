"""Textured Workbench views of a Custodian blend with a given base colour image. Args: -- <blend> <basecolor png>
<out prefix>"""
import bpy, os, sys, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc
src, img, prefix = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=cc.path(src))
ob = bpy.data.objects['Custodian']
mat = bpy.data.materials.new('Tex'); mat.use_nodes = True
tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(cc.path(img))
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
ob.data.materials.clear(); ob.data.materials.append(mat)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('Energy'):
        pass
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 800
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
views = {'front': (Vector((0, -1, 0.05)), Vector((0, 0, 1.7)), 4.0), 'below': (Vector((0, -0.35, -1)), Vector((0, -0.2, 0.7)), 3.2),
         'eye': (Vector((0, -1, 0)), Vector((0, -1.0, 1.84)), 1.2), 'back': (Vector((0, 1, 0.1)), Vector((0, 0, 1.7)), 4.0),
         'left': (Vector((1, 0, 0.1)), Vector((0, -0.3, 1.6)), 4.0), 'sensor': (Vector((-0.5, -1, 0.3)), Vector((0, -0.1, 3.0)), 0.9)}
for k, (d, c, s) in views.items():
    cam.data.ortho_scale = s
    d = d.normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = cc.path(f'{prefix}_{k}.png'); bpy.ops.render.render(write_still=True)
