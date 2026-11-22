"""Survey (Blender): for each source GLB list its mesh objects (triangles, materials, blend modes), actions and
bounds in the Standing pose, and render a workbench front and side view of every mesh and of the opaque meshes only.
Usage: blender -b --python survey.py -- <out_dir> <glb> [<glb> ...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]
os.makedirs(out, exist_ok=True)
for path in argv[1:]:
    tag = os.path.basename(path)[:-4]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    sc = bpy.context.scene
    arm = next((o for o in sc.objects if o.type == 'ARMATURE'), None)
    print('==', tag, 'actions', [(a.name, int(a.frame_range[1])) for a in bpy.data.actions])
    if arm and 'Standing' in bpy.data.actions:
        if arm.animation_data is None:
            arm.animation_data_create()
        act = bpy.data.actions['Standing']
        arm.animation_data.action = act
        if hasattr(arm.animation_data, 'action_slot') and len(act.slots):
            arm.animation_data.action_slot = act.slots[0]
        sc.frame_set(0)
    dg = bpy.context.evaluated_depsgraph_get()
    meshes = [o for o in sc.objects if o.type == 'MESH']
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in meshes:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        t = sum(len(p.vertices) - 2 for p in me.polygons)
        ps = [o.matrix_world @ v.co for v in me.vertices]
        if ps:
            olo = Vector([min(p[i] for p in ps) for i in range(3)]); ohi = Vector([max(p[i] for p in ps) for i in range(3)])
            lo = Vector([min(lo[i], olo[i]) for i in range(3)]); hi = Vector([max(hi[i], ohi[i]) for i in range(3)])
        mats = []
        for m in o.data.materials:
            if m is None:
                continue
            mats.append((m.name, getattr(m, 'surface_render_method', '?'), getattr(m, 'blend_method', '?')))
        print('  MESH', o.name, 'tris', t, 'mats', mats, 'bounds', tuple(round(x, 2) for x in olo), tuple(round(x, 2) for x in ohi))
        ev.to_mesh_clear()
    print('  BOUNDS', tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'MATERIAL'
    sc.render.resolution_x, sc.render.resolution_y = 420, 560
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = 'ORTHO'
    size = max(hi - lo) * 1.15
    cam.data.ortho_scale = size
    c = (lo + hi) / 2
    for view, d in (('front', Vector((0, -1, 0))), ('side', Vector((1, 0, 0))), ('front2', Vector((0, 1, 0))),
                    ('side2', Vector((-1, 0, 0)))):
        cam.location = c + d * size * 3
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{tag}_{view}.png')
        bpy.ops.render.render(write_still=True)
print('SURVEY_DONE')
