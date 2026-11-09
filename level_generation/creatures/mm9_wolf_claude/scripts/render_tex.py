"""Render 'Body' of a blend in the bind pose textured with a given image (AO, class map) from views.
Args: <blend> <image> <outdir> <prefix> <views comma> [size] [ortho]"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
blend, image, outdir, prefix, views = argv[:5]
size = int(argv[5]) if len(argv) > 5 else 512
ortho = float(argv[6]) if len(argv) > 6 else 4.0
bpy.ops.wm.open_mainfile(filepath=blend)
for rig in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
ob = bpy.data.objects['Body']
mat = bpy.data.materials.new('t'); mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(image)
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
ob.data.materials.clear(); ob.data.materials.append(mat)
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = size
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
bpy.context.view_layer.update()
pts = [ob.matrix_world @ v.co for v in ob.data.vertices]
c = Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])
dirs = {'q34': (-1, -1.25, 0.55), 'front': (0, -1, 0), 'left': (1, 0, 0), 'right': (-1, 0, 0), 'back': (0, 1, 0),
        'top': (0, 0.0001, 1), 'bottom': (0, 0.0001, -1), 'q34b': (1, 1.25, 0.55)}
os.makedirs(outdir, exist_ok=True)
for v in views.split(','):
    d = Vector(dirs[v]).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
print('RENDERED', prefix)
