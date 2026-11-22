"""Shared posing helpers (Blender): import a creature GLB, pose it from a spec and return its main mesh.

Pose spec (dict): {"base": [action, frame], "overrides": [{"bones": regex, "action": a, "frame": f}, ...],
"tweaks": {bone: [rx, ry, rz] degrees, local, applied after}}. Overrides copy those bones' local transforms
(matrix_basis) from another clip's frame; tweaks rotate single bones by hand."""
import math
import re

import bpy
from mathutils import Euler, Matrix


def import_creature(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    scene = bpy.context.scene
    arm = next(o for o in scene.objects if o.type == 'ARMATURE')
    body = max((o for o in scene.objects if o.type == 'MESH' and o.find_armature() is arm),
               key=lambda o: len(o.data.polygons))
    for o in list(scene.objects):
        if o.type == 'MESH' and o is not body:
            bpy.data.objects.remove(o, do_unlink=True)
    if arm.animation_data is None:
        arm.animation_data_create()
    return arm, body


def _set_action(arm, name, frame):
    act = bpy.data.actions[name]
    arm.animation_data.action = act
    if hasattr(arm.animation_data, 'action_slot') and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(frame), subframe=frame - int(frame))
    return {pb.name: pb.matrix_basis.copy() for pb in arm.pose.bones}


def apply_pose(arm, spec):
    pose = _set_action(arm, *spec['base'])
    for ov in spec.get('overrides', []):
        other = _set_action(arm, ov['action'], ov['frame'])
        rx = re.compile(ov['bones'])
        for name, m in other.items():
            if rx.search(name):
                pose[name] = m
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis = pose[pb.name]
    for name, deg in spec.get('tweaks', {}).items():
        pb = arm.pose.bones[name]
        rot = Euler([math.radians(d) for d in deg], 'XYZ').to_matrix().to_4x4()
        pb.matrix_basis = pb.matrix_basis @ rot
    bpy.context.view_layer.update()


def bake_static(arm, body):
    """Apply the armature: a static mesh in world space, parent and rig removed."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    me.transform(body.matrix_world)
    static = bpy.data.objects.new(body.name + '_static', me)
    bpy.context.scene.collection.objects.link(static)
    for o in list(bpy.context.scene.objects):
        if o is not static:
            bpy.data.objects.remove(o, do_unlink=True)
    static.vertex_groups.clear()
    return static
