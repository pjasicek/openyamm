"""Clay renders of master_motion actions. Usage: blender -b -P clay.py -- <blend> <action> <frames,> <outprefix>"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['Lizardman_Rig']; body = bpy.data.objects['Lizardman_Body']; sc = bpy.context.scene
for t in rig.animation_data.nla_tracks: t.mute = True
act = bpy.data.actions[a[1]]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
for o in list(sc.objects):
    if o.type not in ('MESH', 'ARMATURE'): bpy.data.objects.remove(o, do_unlink=True)
for o in sc.objects:
    if o.type == 'MESH' and o is not body: o.hide_render = True
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.95
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = 520; sc.render.resolution_y = 560
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (.75, .73, .7)
sc.display.shading.show_cavity = True
views = {'front': (0, -1, .08), 'q34': (.75, -.65, .1), 'side': (1, 0, .05), 'back': (-.3, 1, .08), 'rq34': (-.75, -.65, .1)}
for f in [float(x) for x in a[2].split(',')]:
    sc.frame_set(int(f), subframe=f % 1)
    for v, d in views.items():
        c = Vector((0, 0, .9)); cam.location = c + Vector(d).normalized() * 4
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{a[3]}_{int(f):03d}_{v}.png'; bpy.ops.render.render(write_still=True)
