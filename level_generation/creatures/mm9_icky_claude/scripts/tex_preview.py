"""Bind-pose textured renders of uv blend Body (+ Wings): tex_preview.py blend body_tex wing_tex outdir prefix ortho cx,cy,cz views"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
blend, btex, wtex, outdir, prefix, ortho, cen, views = argv
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'ARMATURE':
        if o.animation_data:
            o.animation_data.action = None
        for pb in o.pose.bones:
            pb.matrix_basis.identity()


def mat(path):
    m = bpy.data.materials.new(os.path.basename(path)); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.abspath(path))
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    return m


for name, path in (('Body', btex), ('Wings', wtex)):
    o = bpy.data.objects.get(name)
    if o and path != '-':
        o.data.materials.clear(); o.data.materials.append(mat(path))
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 640; sc.render.film_transparent = True
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float(ortho); cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in cen.split(',')])
dirs = {'q34': (-1.0, -1.25, 0.55), 'front': (0, -1, 0.15), 'left': (1, 0, 0.1), 'below': (0, 0.0001, -1),
        'top': (0, 0.0001, 1), 'right': (-1, 0, 0.1), 'back': (0, 1, 0.3), 'q34l': (1.0, -1.25, 0.55)}
for v in views.split(','):
    d = Vector(dirs[v]).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
