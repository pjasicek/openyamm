"""Render every LOD of the split models: standing pose, three views, textured studio Workbench, transparent film.

Usage: blender -b -P lod_render.py -- <split_dir> <stem,...>
Writes <split_dir>/<stem>/lod<N>_<view>.png at 512x512; the camera frames LOD0's posed bounds and stays fixed.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
split_dir = args[0]
stems = args[1].split(',')
VIEWS = (('front', (0, -1, 0.15)), ('q34', (0.75, -0.75, 0.3)), ('side', (1, 0, 0.15)))


def pick_action():
    actions = list(bpy.data.actions)
    role = 'Forge_Standing' if 'forgemaster' in split_dir else 'Carbine_Standing'
    for action in actions:
        if role in action.name:
            return action
    for wanted in ('standing', 'stand', 'idle', 'fidget', 'walk'):
        for action in actions:
            if wanted in action.name.lower():
                return action
    return actions[0] if actions else None


def posed_bounds():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    skinned = [o for o in meshes if any(m.type == 'ARMATURE' for m in o.modifiers)]
    for obj in skinned or meshes:
        if obj.hide_render:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        for vertex in mesh.vertices:
            point = evaluated.matrix_world @ vertex.co
            lo = Vector(map(min, lo, point))
            hi = Vector(map(max, hi, point))
        evaluated.to_mesh_clear()
    return lo, hi


for stem in stems:
    folder = os.path.join(split_dir, stem)
    levels = sorted(int(n[3:-4]) for n in os.listdir(folder) if n.startswith('lod') and n.endswith('.glb'))
    frame = None
    for level in levels:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        try:
            bpy.ops.import_scene.gltf(filepath=os.path.join(folder, f'lod{level}.glb'))
        except Exception as error:
            print(f'LODRENDER fail {stem} {level} {error}')
            break
        action = pick_action()
        for obj in scene.objects:
            if obj.type == 'ARMATURE' and action is not None:
                if obj.animation_data is None:
                    obj.animation_data_create()
                obj.animation_data.action = action
                if hasattr(obj.animation_data, 'action_slot') and action.slots:
                    obj.animation_data.action_slot = action.slots[0]
        scene.frame_set(0)
        if frame is None:
            frame = posed_bounds()
        lo, hi = frame
        centre = (lo + hi) * 0.5
        diagonal = max(hi - lo) * 1.15
        camera = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
        scene.collection.objects.link(camera)
        scene.camera = camera
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = diagonal
        camera.data.clip_end = diagonal * 10
        scene.render.engine = 'BLENDER_WORKBENCH'
        scene.display.shading.light = 'STUDIO'
        scene.display.shading.color_type = 'TEXTURE'
        scene.render.film_transparent = True
        scene.view_settings.view_transform = 'Standard'
        scene.render.resolution_x = scene.render.resolution_y = 512
        scene.render.image_settings.color_mode = 'RGBA'
        for view, direction in VIEWS:
            camera.location = centre + Vector(direction).normalized() * diagonal * 3
            camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = os.path.join(folder, f'lod{level}_{view}.png')
            bpy.ops.render.render(write_still=True)
    print(f'LODRENDER done {stem}')

sys.stdout.flush();os._exit(0)
