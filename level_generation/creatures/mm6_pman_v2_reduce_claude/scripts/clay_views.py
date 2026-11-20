"""Clay (workbench, cavity) views of the master's Body at rest: whole, face, hands. Usage: blender -b -P clay_views.py -- <blend> <label>"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name != os.environ.get('CLAY_OBJ', 'Body')
B = lambda n: rig.matrix_world @ rig.pose.bones[n].head
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.show_cavity = True
sc.display.shading.color_type = 'SINGLE'; sc.render.resolution_x = sc.render.resolution_y = 600
spots = {'whole': (Vector((0, 0, .85)), 1.9), 'face': (B('B_Head') + Vector((0, 0, .08)), .32), 'handR': (B('B_R_Hand'), .25), 'handL': (B('B_L_Hand'), .25)}
for spot, (c, size) in spots.items():
    for view, d in {'front': (0, -1, .05), 'q34': (.7, -.7, .15), 'side': (1, 0, .05), 'back': (0, 1, .05)}.items():
        dv = Vector(d).normalized(); cam.location = c + dv * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
        sc.render.filepath = os.path.join(HERE, 'review', 'r45', f'{label}_{spot}_{view}.png'); bpy.ops.render.render(write_still=True)
