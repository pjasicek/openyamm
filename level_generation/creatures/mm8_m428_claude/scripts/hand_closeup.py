"""Right-hand close-ups (front, side from her right, back) at given clip frames, with the review dagger mesh.
Clay (Workbench) with a distinct palm colour: vertices of the right hand whose rest normal faces the rest palm
direction (forward) are tinted orange so palm vs back of the hand reads at a glance.
Args: -- <blend> <out prefix> <action>:<frame> [...]"""
import bpy, sys, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = bpy.data.objects.get('Body') or bpy.data.objects.get('M428')
me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
g = body.vertex_groups
rh = {g[n].index for n in g.keys() if n.startswith('B_R_Hand') or n.startswith('B_R_Finger')}
col = me.color_attributes.new('palm', 'BYTE_COLOR', 'POINT')
for v in me.vertices:
    w = sum(e.weight for e in v.groups if e.group in rh)
    palm = w > 0.5 and v.normal.y < -0.3
    col.data[v.index].color = (0.95, 0.45, 0.1, 1) if palm else (0.75, 0.75, 0.75, 1)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_cavity = False
sh.background_type = 'VIEWPORT'; sh.background_color = (0.3, 0.32, 0.35)
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.45
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for spec in a[2:]:
    name, f = spec.split(':'); act = bpy.data.actions[name]
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(f))
    c = rig.matrix_world @ rig.pose.bones['B_R_Hand'].head
    for view, d in (('front', Vector((0, -1, 0))), ('side', Vector((-1, 0, 0))), ('back', Vector((0, 1, 0)))):
        cam.location = c + d * 2
        cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); cam.rotation_euler.rotate_axis('Y', 0)
        q = (-d).to_track_quat('-Z', 'Y'); cam.rotation_euler = q.to_euler()
        sc.render.filepath = f'{out}_{name}{int(f):03d}_{view}.png'; bpy.ops.render.render(write_still=True)
