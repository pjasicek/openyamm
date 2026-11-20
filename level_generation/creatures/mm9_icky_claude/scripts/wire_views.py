"""Solid + wireframe renders of Body (and Wings) in the bind pose. Args: blend outdir prefix ortho cx,cy,cz views"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
blend, outdir, prefix, ortho, cen, views = argv
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'ARMATURE':
        if o.animation_data:
            o.animation_data.action = None
        for pb in o.pose.bones:
            pb.matrix_basis.identity()
    if o.type == 'MESH' and o.name not in ('Body', 'Wings') and not o.name.startswith('Icky'):
        o.hide_render = True
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_backface_culling = True
sc.display.shading.single_color = (0.75, 0.75, 0.72)
sc.render.resolution_x = sc.render.resolution_y = 640; sc.render.film_transparent = True
sh.show_object_outline = False
for o in sc.objects:
    if o.type == 'MESH' and not o.hide_render:
        o.show_wire = True
sc.display.shading.show_cavity = False
try:
    sc.display.render_aa = '8'
except Exception:
    pass
# wireframe overlay via a wireframe modifier copy is heavy; use Freestyle-less workbench wire: object show_wire
# does not render, so add a Wireframe-modifier duplicate in dark colour
mat = bpy.data.materials.new('wire'); mat.diffuse_color = (0.05, 0.05, 0.05, 1)
for o in list(sc.objects):
    if o.type == 'MESH' and not o.hide_render:
        d = o.copy(); d.data = o.data.copy(); sc.collection.objects.link(d)
        m = d.modifiers.new('wf', 'WIREFRAME'); m.thickness = 0.0006; m.use_replace = True
        d.data.materials.clear(); d.data.materials.append(mat)
sh.color_type = 'MATERIAL'
gray = bpy.data.materials.new('g'); gray.diffuse_color = (0.75, 0.75, 0.72, 1)
for o in sc.objects:
    if o.type == 'MESH' and not o.hide_render and not any(m.type == 'WIREFRAME' for m in o.modifiers):
        o.data.materials.clear(); o.data.materials.append(gray)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float(ortho); cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in cen.split(',')])
dirs = {'q34': (-1.0, -1.25, 0.55), 'front': (0, -1, 0), 'left': (1, 0, 0), 'below': (0, 0.0001, -1),
        'top': (0, 0.0001, 1), 'right': (-1, 0, 0), 'back': (0, 1, 0)}
for v in views.split(','):
    d = Vector(dirs[v]).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
