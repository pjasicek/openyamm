"""Pose survey (Blender, background): import a creature GLB and render a three-quarter view of each clip at a few
frames, so a guardian pose can be chosen. Usage: blender -b --python pose_probe.py -- <src.glb> <outdir> [clips...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, outdir = argv[0], argv[1]
only = set(argv[2:])
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in meshes:
    print('MESH', o.name, len(o.data.polygons), [m.name for m in o.data.materials], o.hide_render)
for o in meshes:
    if 'Shadow' in o.name:
        o.hide_render = True
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.6, 0.6, 0.62)
scene.display.shading.show_cavity = True
scene.render.resolution_x = 320
scene.render.resolution_y = 400
scene.render.film_transparent = False
cam_data = bpy.data.cameras.new('cam')
cam_data.type = 'ORTHO'
cam = bpy.data.objects.new('cam', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
if arm.animation_data is None:
    arm.animation_data_create()


def frame_bounds():
    dg = bpy.context.evaluated_depsgraph_get()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in meshes:
        if 'Shadow' in o.name:
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            w = ev.matrix_world @ v.co
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
        ev.to_mesh_clear()
    return lo, hi


for act in bpy.data.actions:
    if only and act.name not in only:
        continue
    arm.animation_data.action = act
    if hasattr(arm.animation_data, 'action_slot') and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    print('ACTION', act.name, f0, f1)
    for i, t in enumerate((0.0, 0.33, 0.66, 1.0)):
        f = int(round(f0 + (f1 - f0) * t))
        scene.frame_set(f)
        lo, hi = frame_bounds()
        centre = (lo + hi) / 2
        size = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
        for view, az in (('q', -35.0), ('s', -90.0)):
            a = math.radians(az)
            # creatures face -Y: the camera stands at -Y, turned by az about z
            d = Vector((math.sin(a) * -1, -math.cos(a), 0.15)).normalized()
            if view == 'q':
                d = Vector((math.sin(math.radians(35)), -math.cos(math.radians(35)), 0.15)).normalized()
            else:
                d = Vector((1, 0, 0.1)).normalized()
            cam.location = centre + d * size * 3
            cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
            cam_data.ortho_scale = size * 1.15
            scene.render.filepath = os.path.join(outdir, f'{act.name}_{i}_{view}.png')
            bpy.ops.render.render(write_still=True)
print('PROBE_DONE')
