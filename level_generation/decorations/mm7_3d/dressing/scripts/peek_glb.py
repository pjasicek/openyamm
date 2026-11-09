"""Quick look at source GLBs: import, report meshes/armature/actions/triangles, render front + side.
Usage: blender -b --python peek_glb.py -- out_dir file.glb [file.glb ...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]
for path in args[1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    name = os.path.splitext(os.path.basename(path))[0]
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('Icosphere')]
    for o in [o for o in bpy.data.objects if o.name.startswith('Icosphere')]:
        bpy.data.objects.remove(o)
    arm = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    print('PEEK', name, 'meshes', [(o.name, len(o.data.polygons)) for o in meshes][:12], 'tris', tris,
          'arm', [(a.name, len(a.data.bones)) for a in arm], 'actions', [a.name for a in bpy.data.actions][:30],
          'mats', [m.name for m in bpy.data.materials][:10])
    for a in arm:
        a.animation_data_clear() if a.animation_data else None
        for pb in a.pose.bones:
            pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = scene.render.resolution_y = 400
    scene.render.film_transparent = True
    world = bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.8, 0.8, 0.8, 1)
    deps = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        ev = o.evaluated_get(deps)
        pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    print('BOUNDS', name, tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
    c = (lo + hi) / 2; r = (hi - lo).length / 2
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); scene.collection.objects.link(cam); scene.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = r * 2.1
    for yaw in (0, 90, 180):
        y = math.radians(yaw)
        d = Vector((math.sin(y), -math.cos(y), 0.1)).normalized()
        cam.location = c + d * r * 4
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(out, f'{name}_y{yaw:03d}.png')
        bpy.ops.render.render(write_still=True)
