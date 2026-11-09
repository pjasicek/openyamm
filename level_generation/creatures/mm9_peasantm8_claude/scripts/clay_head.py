"""Clay head views of a master blend's Body at rest (ear and head shape checks). Args (Blender): <blend> <out prefix>
Writes <prefix>_0..4.png: front, character's right side... (+x side), -x side, 3/4 back, back."""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        if o.animation_data: o.animation_data.action = None
        for b in o.pose.bones: b.matrix_basis.identity()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.render.resolution_x = sc.render.resolution_y = 400
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.4, 0.4, 0.4)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[2]) if len(a) > 2 else 0.34
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in a[3].split(',')]) if len(a) > 3 else Vector((-0.017, 0.01, 0.77))
for k, dv in enumerate([(0, -1, 0), (-1, 0, 0), (1, 0, 0), (-1, 1, 0.3), (0, 1, 0)]):
    dv = Vector(dv).normalized(); cam.location = c + dv * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = a[1] + f'_{k}.png'; bpy.ops.render.render(write_still=True)
