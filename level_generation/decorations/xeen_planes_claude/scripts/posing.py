"""Posing helpers (Blender): import a creature GLB, keep the meshes and material faces a statue uses, pose it from a
spec and bake the pose into one static mesh.

Pose spec: {"base": [action, frame], "overrides": [{"bones": regex, "action": a, "frame": f}],
"rot": [[bone, axis, degrees] or [bone, "aim", [x, y, z]], ...]  rotations about a world axis ("x", "y", "z" or [x, y, z]) through the bone's
head, applied in order (children follow), "coil": {"bones": regex, "axis": "z", "degrees": per-bone angle,
"grow": factor per bone}}. The creatures face Blender -Y; their left is +X."""
import math
import re

import bmesh
import bpy
from mathutils import Matrix, Vector

AXES = {'x': Vector((1, 0, 0)), 'y': Vector((0, 1, 0)), 'z': Vector((0, 0, 1))}


def import_creature(path, mesh_regex, material_regex):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    scene = bpy.context.scene
    arm = next(o for o in scene.objects if o.type == 'ARMATURE')
    keep_mesh, keep_mat = re.compile(mesh_regex), re.compile(material_regex)
    bodies = []
    for o in list(scene.objects):
        if o.type != 'MESH':
            continue
        if not keep_mesh.search(o.name):
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        mats = o.data.materials
        drop = [f for f in bm.faces if not (mats and mats[f.material_index] and keep_mat.search(mats[f.material_index].name))]
        bmesh.ops.delete(bm, geom=drop, context='FACES')
        bm.to_mesh(o.data)
        bm.free()
        if len(o.data.polygons):
            bodies.append(o)
        else:
            bpy.data.objects.remove(o, do_unlink=True)
    if arm.animation_data is None:
        arm.animation_data_create()
    return arm, bodies


def _set_action(arm, name, frame):
    act = bpy.data.actions[name]
    arm.animation_data.action = act
    if hasattr(arm.animation_data, 'action_slot') and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(frame), subframe=frame - int(frame))
    return {pb.name: pb.matrix_basis.copy() for pb in arm.pose.bones}


def _axis(a):
    return AXES[a].copy() if isinstance(a, str) else Vector(a).normalized()


def rotate_world(arm, bone, axis, degrees):
    """Rotate a pose bone about a world axis through its head (children follow)."""
    pb = arm.pose.bones[bone]
    head = pb.head.copy()                      # armature space
    a = arm.matrix_world.to_3x3().inverted() @ _axis(axis)
    r = Matrix.Translation(head) @ Matrix.Rotation(math.radians(degrees), 4, a) @ Matrix.Translation(-head)
    pb.matrix = r @ pb.matrix
    bpy.context.view_layer.update()


def aim(arm, bone, direction):
    """Turn a pose bone (minimal rotation about its head) so it points along a world direction."""
    pb = arm.pose.bones[bone]
    cur = (arm.matrix_world.to_3x3() @ (pb.tail - pb.head)).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    axis, ang = q.to_axis_angle()
    if ang > 1e-6:
        rotate_world(arm, bone, list(axis), math.degrees(ang))


def lift(arm, bone, degrees):
    """Tilt a pose bone up (positive) or down about the horizontal axis across its direction."""
    pb = arm.pose.bones[bone]
    d = (arm.matrix_world.to_3x3() @ (pb.tail - pb.head)).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-6:
        return
    rotate_world(arm, bone, list(side.normalized()), degrees)


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
    bpy.context.view_layer.update()
    for bone, axis, deg in spec.get('rot', []):
        if axis == 'aim':
            aim(arm, bone, deg)
        elif axis == 'lift':
            lift(arm, bone, deg)
        else:
            rotate_world(arm, bone, axis, deg)
    coil = spec.get('coil')
    if coil:
        rx = re.compile(coil['bones'])
        chain = [b.name for b in arm.data.bones if rx.search(b.name)]
        deg = coil['degrees']
        for name in chain:
            rotate_world(arm, name, coil.get('axis', 'z'), deg)
            deg *= coil.get('grow', 1.0)
        for bone, axis, d in coil.get('then', []):
            if axis == 'lift':
                lift(arm, bone, d)
            else:
                rotate_world(arm, bone, axis, d)


def bake_static(arm, bodies, name='HighFigure'):
    """Apply the armature: one static mesh in world space (all kept meshes joined), rig removed."""
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    mats = []
    for body in bodies:
        ev = body.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
        me.transform(body.matrix_world)
        offset = len(mats)
        mats += list(body.data.materials)
        before = len(bm.faces)
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[before:]:
            f.material_index += offset
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    static = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(static)
    for o in list(bpy.context.scene.objects):
        if o is not static:
            bpy.data.objects.remove(o, do_unlink=True)
    return static
