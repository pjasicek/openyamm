import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['Lizardman_Rig']; body = bpy.data.objects['Lizardman_Body']; sc = bpy.context.scene
for t in rig.animation_data.nla_tracks: t.mute = True
act = bpy.data.actions[a[1]]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
for o in list(sc.objects):
    if o.type not in ('MESH', 'ARMATURE'): bpy.data.objects.remove(o, do_unlink=True)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = .55
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = sc.render.resolution_y = 400
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (.75, .73, .7); sc.display.shading.show_cavity = True
for f in [int(x) for x in a[2].split(',')]:
    sc.frame_set(f)
    for side in ['Left', 'Right']:
        x = 1 if side == 'Left' else -1
        c = rig.matrix_world @ rig.pose.bones[side + 'ForeArm'].head
        c = (c + rig.matrix_world @ rig.pose.bones[side + 'Hand'].head) / 2
        for v, d in {'out': (x, -.15, .05), 'front': (x * .3, -1, .05), 'back': (x * .5, 1, .1)}.items():
            cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f'{a[3]}_{side}_{f:03d}_{v}.png'; bpy.ops.render.render(write_still=True)
