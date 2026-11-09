"""Part-coloured zoomed views for labelling: crop name, centre, ortho scale, view. Args: <blend> <out prefix>"""
import bpy, sys
from mathutils import Vector
BL, PNG = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=BL)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'; sc.display.shading.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 1400
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
CR = dict(torso=((0, .02, .22), .42), pelvis=((0, .02, .03), .3), hand=((-.32, .02, .07), .16), elbow=((-.27, .03, .12), .12), foot=((-.19, -.03, -.47), .2), knee=((-.17, .02, -.3), .3))
V = dict(front=(0, -1, 0), back=(0, 1, 0), right=(-1, 0, 0), left=(1, 0, 0), top=(0, 0, 1), bottom=(0, 0, -1))
for name, (c, s) in CR.items():
    cd.ortho_scale = s
    for v, d in V.items():
        if name in ('elbow', 'knee') and v in ('top', 'bottom'): continue
        cam.location = Vector(c) + Vector(d) * 5
        cam.rotation_euler = (Vector(c) - cam.location).to_track_quat('-Z', 'Z' if v not in ('top', 'bottom') else 'Y').to_euler()
        if v in ('top', 'bottom'):
            cam.rotation_euler = (Vector(c) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        else:
            cam.rotation_euler = (Vector(c) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{PNG}_{name}_{v}.png'
        bpy.ops.render.render(write_still=True)
