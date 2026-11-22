"""Pose survey (Blender): import a creature GLB, keep only the faces whose material matches a regex, and render a
three-quarter and a side view of each clip at four frames; prints the bone names.
Usage: blender -b --python pose_probe.py -- <src.glb> <outdir> <material regex> [clips...]"""
import math
import os
import re
import sys

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, outdir, keep = argv[0], argv[1], re.compile(argv[2])
only = set(argv[3:])
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
print('BONES', ' '.join(b.name for b in arm.data.bones))
meshes = []
for o in list(scene.objects):
    if o.type != 'MESH':
        continue
    if o.name.startswith('Icosphere'):
        bpy.data.objects.remove(o, do_unlink=True)
        continue
    bm = bmesh.new()
    bm.from_mesh(o.data)
    drop = [f for f in bm.faces if not (o.data.materials and o.data.materials[f.material_index]
                                         and keep.search(o.data.materials[f.material_index].name))]
    bmesh.ops.delete(bm, geom=drop, context='FACES')
    bm.to_mesh(o.data)
    bm.free()
    if len(o.data.polygons) == 0:
        bpy.data.objects.remove(o, do_unlink=True)
        continue
    meshes.append(o)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.6, 0.6, 0.62)
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 320, 400
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
    for i, t in enumerate((0.0, 0.33, 0.66, 1.0)):
        f = int(round(f0 + (f1 - f0) * t))
        scene.frame_set(f)
        lo, hi = frame_bounds()
        centre = (lo + hi) / 2
        size = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
        for view, d in (('q', Vector((math.sin(math.radians(35)), -math.cos(math.radians(35)), 0.15))),
                        ('s', Vector((1, 0, 0.1)))):
            d = d.normalized()
            cam.location = centre + d * size * 3
            cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
            cam_data.ortho_scale = size * 1.15
            scene.render.filepath = os.path.join(outdir, f'{act.name}_{i}_{view}.png')
            bpy.ops.render.render(write_still=True)
print('PROBE_DONE')
