"""Clay frames of every clip (six evenly spaced frames per clip, front three-quarter, a floor line) with the lowest
point per frame printed (floor contact). Args: -- <anim.blend> <out dir> [camera azimuth deg]"""
import bpy, os, sys, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc
args = sys.argv[sys.argv.index('--') + 1:]
src, outdir = args[:2]
az = float(args[2]) if len(args) > 2 else -35
bpy.ops.wm.open_mainfile(filepath=cc.path(src))
os.makedirs(cc.path(outdir), exist_ok=True)
sc = bpy.context.scene
rig = bpy.data.objects['Custodian_Rig']; body = bpy.data.objects['Custodian']
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.show_cavity = True; sc.display.shading.single_color = (0.75, 0.72, 0.66)
sc.render.resolution_x = sc.render.resolution_y = 420
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 5.2
a = math.radians(az); d = Vector((math.sin(a), -math.cos(a), 0.25)).normalized()
cam.location = Vector((0, -0.4, 1.6)) + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
for act in bpy.data.actions:
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    zs = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        me = body.evaluated_get(dg).to_mesh()
        zs.append(min(v.co.z for v in me.vertices))
        body.evaluated_get(dg).to_mesh_clear()
    print('MINZ', act.name, 'min %.3f max %.3f' % (min(zs), max(zs)), 'first %.3f last %.3f' % (zs[0], zs[-1]))
    for i, f in enumerate(np.linspace(f0, f1, 6).round().astype(int)):
        sc.frame_set(int(f)); sc.render.filepath = cc.path(f'{outdir}/{act.name}_{i}.png')
        bpy.ops.render.render(write_still=True)
