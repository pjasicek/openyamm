"""G1: preview local Mutant clips on their own mannequin, preserving source timing."""
import json
import math
import os
from pathlib import Path
import sys

import bpy
from mathutils import Vector


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[2]
CLIPS = {
    'Standing': 'Mutant Idle.fbx',
    'Fidget': 'Mutant Breathing Idle.fbx',
    'Walking': 'Mutant Walking.fbx',
    'Running': 'Mutant Run.fbx',
    'Attack': 'Mutant Punch.fbx',
    'AttackSwiping': 'Mutant Swiping.fbx',
    'Hit': 'Hit Reaction (4).fbx',
    'Death': 'Mutant Dying.fbx',
    'Cast': 'Mutant Roaring.fbx',
}


def bounds(meshes):
    points = []
    deps = bpy.context.evaluated_depsgraph_get()
    for obj in meshes:
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        points.extend(obj.matrix_world @ v.co for v in mesh.vertices)
        evaluated.to_mesh_clear()
    assert points
    return Vector(tuple(min(p[i] for p in points) for i in range(3))), Vector(
        tuple(max(p[i] for p in points) for i in range(3)))


def run():
    output = PROJECT / 'review/source_clips'
    output.mkdir(parents=True, exist_ok=True)
    records = {}
    for role, filename in CLIPS.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(REPO / 'anim_library/mixamo/characters/warrok_w_kurniawan.fbx'))
        rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
        assert meshes
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(REPO / 'anim_library/mixamo' / filename))
        source = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
        assert list(source.data.bones.keys()) == list(rig.data.bones.keys()), filename
        rest_error = max(max(abs(a - b) for a, b in zip(
            [v for row in source.data.bones[n].matrix_local for v in row],
            [v for row in rig.data.bones[n].matrix_local for v in row])) for n in rig.data.bones.keys())
        angles = [source.data.bones[n].matrix_local.to_quaternion().rotation_difference(
            rig.data.bones[n].matrix_local.to_quaternion()).angle for n in rig.data.bones.keys()]
        rest_angle = max(min(abs(a), abs(2 * math.pi - a)) for a in angles)
        print('REST', filename, 'position matrix delta', rest_error, 'angle radians', rest_angle, flush=True)
        # shortcut: mannequin rest differs by about 1 degree; production uses world-rotation retargeting.
        assert rest_angle < math.radians(2), (filename, rest_angle)
        action = source.animation_data.action
        slot = source.animation_data.action_slot
        rig.animation_data.action = action
        if slot:
            rig.animation_data.action_slot = slot
        bpy.data.objects.remove(source, do_unlink=True)
        scene = bpy.context.scene
        fps = scene.render.fps / scene.render.fps_base
        start, end = action.frame_range
        assert end > start
        frames = [start + (end - start) * t for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        source_positions = []
        for frame in range(int(start), int(end) + 1):
            scene.frame_set(frame)
            source_positions.append({
                'time': (frame - start) / fps,
                'joints': {name: list(rig.matrix_world @ rig.pose.bones['mixamorig:' + name].head)
                           for name in ('Hips', 'Head', 'LeftHand', 'RightHand', 'LeftFoot', 'RightFoot')},
            })
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'
        scene.cycles.samples = 8
        scene.cycles.use_denoising = True
        scene.render.resolution_x = 280
        scene.render.resolution_y = 340
        scene.render.resolution_percentage = 100
        scene.world = bpy.data.worlds.new('World')
        scene.world.use_nodes = True
        scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.16, 0.17, 0.19, 1)
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.7
        mat = bpy.data.materials.new('Clay')
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (0.45, 0.48, 0.52, 1)
        bsdf.inputs['Roughness'].default_value = 0.85
        for mesh in meshes:
            mesh.data.materials.clear()
            mesh.data.materials.append(mat)
        scene.frame_set(int(start))
        lo, hi = bounds(meshes)
        height = max(hi.z - lo.z, 2.0)
        for location, energy, size in (((-3, -4, 5), 700, 5), ((3, 2, 4), 600, 4)):
            data = bpy.data.lights.new('Key', 'AREA')
            data.energy, data.shape, data.size = energy, 'DISK', size
            light = bpy.data.objects.new('Key', data)
            scene.collection.objects.link(light)
            light.location = location
            light.rotation_euler = (Vector((0, 0, height / 2)) - light.location).to_track_quat('-Z', 'Y').to_euler()
        cam_data = bpy.data.cameras.new('Camera')
        cam_data.type = 'ORTHO'
        cam = bpy.data.objects.new('Camera', cam_data)
        scene.collection.objects.link(cam)
        scene.camera = cam
        images = []
        for number, frame in enumerate(frames):
            scene.frame_set(int(frame), subframe=frame - int(frame))
            lo, hi = bounds(meshes)
            center = (lo + hi) * 0.5
            cam_data.ortho_scale = max(height * 1.25, (hi - lo).length * 1.15)
            for view, offset in (('front', Vector((0, -8, 0))), ('left', Vector((8, 0, 0)))):
                cam.location = center + offset
                cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
                path = output / f'{role}_{number}_{view}.png'
                scene.render.filepath = str(path)
                bpy.ops.render.render(write_still=True)
                assert path.is_file(), path
                images.append(str(path.relative_to(PROJECT)))
        records[role] = {'file': 'anim_library/mixamo/' + filename,
                         'duration': (end - start) / fps, 'source_rest_error': rest_error, 'source_rest_angle_degrees': math.degrees(rest_angle),
                         'samples': source_positions, 'images': images}
        (output / 'manifest.json').write_text(json.dumps(records, indent=2) + '\n')
        print('G1_PREVIEW', role, 'duration', records[role]['duration'], flush=True)
    assert len(records) == len(CLIPS)


try:
    run()
except BaseException:
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
