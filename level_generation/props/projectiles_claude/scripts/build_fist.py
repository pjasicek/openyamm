"""Flying Fist (object 7090, sprite spell76: an ice-blue clenched fist with a forearm that frays into icy shards)
-> work/fist_export.glb, installed as engine/models/projectile_fist.glb.

1. An MPFB (MakeHuman, CC0) human with the `default` rig; its right hand curled into a fist: fingers 2-5 flexed at all
   three joints toward the palm normal (the sign of each bone's local X found by test, as mm6_cle_claude/hands_mpfb.py),
   the thumb's base solved so its tip rests on the outside of the middle and index fingers' middle segments.
2. Cut from the posed mesh: the hand (wrist, metacarpal and finger weights) and the forearm up to FOREARM hand
   lengths back from the wrist; the cut is filled and hidden in a crown of thin ice crystals pointing back (the
   sprite's frayed wrist).
3. Turned so the knuckles lead (-Y), the back of the hand up; decimated to TRIANGLES.
4. Material Ice: the near-uniform saturated ice blue (fist_ice) on box UVs, glossy with a cold glow (the enhanced
   effect's red-orange light turned a paler blue pink); COLOR_0 holds ray-cast occlusion so the fingers read.
Usage: blender --background --factory-startup --python build_fist.py"""
import math
import os
import random
import sys

import addon_utils
import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import projlib as pl  # noqa: E402

# Forearm kept behind the wrist, in hand lengths (wrist to middle knuckle).
FOREARM = 0.55
TRIANGLES = 1300
FINGERS = {f: [f'finger{f}-{j}.R' for j in (1, 2, 3)] for f in range(1, 6)}
HAND_BONES = ['wrist.R'] + [f'metacarpal{i}.R' for i in range(1, 5)] + [b for f in FINGERS.values() for b in f]
# Fist: degrees at the knuckle, middle and end joint per finger (index to pinky).
CURL = {2: (82, 100, 60), 3: (86, 102, 62), 4: (88, 104, 62), 5: (90, 104, 60)}
# Thumb end joints' flex toward the palm in degrees; its base is solved (solve_thumb).
THUMB_FLEX = [('finger1-2.R', 20), ('finger1-3.R', 30)]


def human():
    addon_utils.enable('bl_ext.blender_org.mpfb', default_set=True)
    from bl_ext.blender_org.mpfb.services.humanservice import HumanService
    body = HumanService.create_human()
    rig = HumanService.add_builtin_rig(body, 'default')
    mask = next(m for m in body.modifiers if m.type == 'MASK')
    mask.show_viewport = mask.show_render = False
    return body, rig, mask.vertex_group


def joint(rig, name, tail=False):
    bone = rig.pose.bones[name]
    return rig.matrix_world @ (bone.tail if tail else bone.head)


def flex_sign(rig, bone, normal):
    """+1 when a positive local X rotation moves the bone's tail toward the palm normal."""
    pose = rig.pose.bones[bone]
    pose.rotation_mode = 'XYZ'
    before = joint(rig, bone, True)
    pose.rotation_euler = (0.3, 0, 0)
    bpy.context.view_layer.update()
    after = joint(rig, bone, True)
    pose.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    return 1.0 if (after - before).dot(normal) > 0 else -1.0


def pose_fist(rig):
    wrist = joint(rig, 'wrist.R')
    knuckle = joint(rig, 'finger3-1.R')
    heading = (knuckle - wrist).normalized()
    across = joint(rig, 'finger2-1.R') - joint(rig, 'finger5-1.R')
    across = (across - heading * across.dot(heading)).normalized()
    palm = across.cross(heading).normalized()
    for finger, angles in CURL.items():
        for bone, degrees in zip(FINGERS[finger], angles):
            sign = flex_sign(rig, bone, palm)
            rig.pose.bones[bone].rotation_euler = (sign * math.radians(degrees), 0, 0)
    for bone, flex in THUMB_FLEX:
        sign = flex_sign(rig, bone, palm)
        rig.pose.bones[bone].rotation_euler = (sign * math.radians(flex), 0, 0)
    bpy.context.view_layer.update()
    solve_thumb(rig, (knuckle - wrist).length)
    return wrist, heading, across, palm


def solve_thumb(rig, hand_length):
    """Turn the thumb's base so its tip rests on the outside of the middle finger's middle segment (the curled
    fingers' front), coarse to fine over its local XYZ rotation."""
    middle = (joint(rig, 'finger3-2.R') + joint(rig, 'finger3-2.R', True)) * 0.5
    index = (joint(rig, 'finger2-2.R') + joint(rig, 'finger2-2.R', True)) * 0.5
    centre = (joint(rig, 'metacarpal3.R') + joint(rig, 'metacarpal3.R', True)) * 0.5
    target = middle * 0.6 + index * 0.4
    target = target + (target - centre).normalized() * hand_length * 0.12
    base = rig.pose.bones['finger1-1.R']
    base.rotation_mode = 'XYZ'

    def error(angles):
        base.rotation_euler = angles
        bpy.context.view_layer.update()
        return (joint(rig, 'finger1-3.R', True) - target).length

    best = (0.0, 0.0, 0.0)
    best_error = error(best)
    for step in (20.0, 8.0, 3.0):
        centre_angles = best
        span = [i * step for i in range(-3, 4)] if step == 20.0 else [i * step for i in range(-2, 3)]
        for dx in span:
            for dy in span:
                for dz in span:
                    angles = tuple(c + math.radians(d) for c, d in zip(centre_angles, (dx, dy, dz)))
                    value = error(angles)
                    if value < best_error:
                        best, best_error = angles, value
    base.rotation_euler = best
    bpy.context.view_layer.update()
    print('THUMB', [round(math.degrees(a)) for a in best], 'tip error', round(best_error / hand_length, 3))


def cut(body, rig, body_group, wrist, heading):
    """The posed hand and forearm stub as a new bmesh (MPFB metres, world space)."""
    names = {group.index: group.name for group in body.vertex_groups}
    keep = set()
    for vertex in body.data.vertices:
        weights = {names[g.group]: g.weight for g in vertex.groups}
        if weights.get(body_group, 0.0) < 0.5:
            continue
        hand = sum(weights.get(b, 0.0) for b in HAND_BONES)
        forearm = weights.get('lowerarm02.R', 0.0) + weights.get('lowerarm01.R', 0.0)
        if hand > 0.3 or forearm > 0.3:
            keep.add(vertex.index)
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    evaluated.to_mesh_clear()
    bm.transform(body.matrix_world)
    bm.verts.ensure_lookup_table()
    hand_length = (joint(rig, 'finger3-1.R') - wrist).length
    drop = [v for v in bm.verts if v.index not in keep or (v.co - wrist).dot(heading) < -FOREARM * hand_length]
    bmesh.ops.delete(bm, geom=drop, context='VERTS')
    # Loose crumbs (separate eyebrow/nail islands) go; the largest piece stays.
    pieces = []
    seen = set()
    for vertex in bm.verts:
        if vertex in seen:
            continue
        stack, piece = [vertex], []
        seen.add(vertex)
        while stack:
            current = stack.pop()
            piece.append(current)
            for edge in current.link_edges:
                other = edge.other_vert(current)
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        pieces.append(piece)
    pieces.sort(key=len)
    for piece in pieces[:-1]:
        bmesh.ops.delete(bm, geom=piece, context='VERTS')
    return bm


def orient(bm, wrist, heading, across, palm):
    """Knuckles to -Y, back of the hand to +Z, centred on the bounds."""
    basis = Matrix((across, -heading, -palm)).to_4x4()     # rows: new X, Y, Z in old coordinates
    bm.transform(basis @ Matrix.Translation(-wrist))
    points = [v.co for v in bm.verts]
    centre = Vector([(min(p[i] for p in points) + max(p[i] for p in points)) / 2 for i in range(3)])
    bm.transform(Matrix.Translation(-centre))


def crystals(bm, uv_layer, rng):
    """A crown of ice crystals round the forearm's cut end, pointing back and outward."""
    points = [v.co for v in bm.verts]
    back = max(p.y for p in points)
    rim = [p for p in points if p.y > back - 0.01]
    centre = sum(rim, Vector()) / len(rim)
    radius = max((Vector((p.x, 0, p.z)) - Vector((centre.x, 0, centre.z))).length for p in rim)
    for k in range(10):
        angle = 2.0 * math.pi * k / 10 + rng.uniform(-0.2, 0.2)
        out = Vector((math.cos(angle), 0.0, math.sin(angle)))
        base = Vector((centre.x, back - radius * 0.3, centre.z)) + out * radius * rng.uniform(0.45, 0.85)
        direction = Vector((0.0, 1.0, 0.0)) + out * rng.uniform(0.1, 0.3)
        crystal(bm, uv_layer, base, direction, radius * rng.uniform(0.14, 0.22), radius * rng.uniform(1.6, 3.0),
                radius * 0.25, 4)


def crystal(bm, uv_layer, base, direction, radius, front, back, sides):
    direction = direction.normalized()
    side = direction.orthogonal().normalized()
    up = direction.cross(side)
    ring = [base + (side * math.cos(2 * math.pi * k / sides) + up * math.sin(2 * math.pi * k / sides)) * radius
            for k in range(sides)]
    tip, tail = base + direction * front, base - direction * back
    for k in range(sides):
        a, b = ring[k], ring[(k + 1) % sides]
        pl.add_face(bm, uv_layer, [(tip, (0.5, 1.0)), (a, (k / sides, 0.3)), (b, ((k + 1) / sides, 0.3))])
        pl.add_face(bm, uv_layer, [(tail, (0.5, 0.0)), (b, ((k + 1) / sides, 0.3)), (a, (k / sides, 0.3))])


def occlusion(obj, rays=32, distance=0.05, strength=0.85):
    """Ray-cast ambient occlusion per vertex into COLOR_0."""
    mesh = obj.data
    tree = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    rng = np.random.default_rng(3)
    directions = rng.normal(size=(rays, 3))
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    attribute = mesh.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    for vertex in mesh.vertices:
        normal = vertex.normal
        hits = 0
        total = 0
        for d in directions:
            direction = Vector(d)
            if direction.dot(normal) < 0:
                direction = -direction
            total += 1
            location, _, _, _ = tree.ray_cast(vertex.co + normal * 1e-4, direction, distance)
            if location is not None:
                hits += 1
        shade = 1.0 - strength * hits / total
        attribute.data[vertex.index].color = (shade, shade, shade, 1.0)
    mesh.color_attributes.active_color = attribute


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    body, rig, body_group = human()
    wrist, heading, across, palm = pose_fist(rig)
    bm = cut(body, rig, body_group, wrist, heading)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    orient(bm, wrist, heading, across, palm)
    for layer in list(bm.loops.layers.uv):
        bm.loops.layers.uv.remove(layer)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new('Fist')
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new('Fist', mesh)
    bpy.context.scene.collection.objects.link(obj)
    decimate = obj.modifiers.new('Decimate', 'DECIMATE')
    decimate.ratio = min(1.0, TRIANGLES / len(mesh.polygons))
    with bpy.context.temp_override(object=obj, active_object=obj):
        bpy.ops.object.modifier_apply(modifier=decimate.name)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.new('UVMap')
    crystals(bm, uv_layer, random.Random(4))
    bm.normal_update()
    pl.box_uv(bm, uv_layer, 0.08)
    bpy.data.objects.remove(obj)
    obj = pl.to_object('Fist', bm, [pl.material('Ice', 'fist_ice', 0.25)], 50)
    occlusion(obj)
    ys = [v.co.y for v in obj.data.vertices]
    print('LENGTH fist (model units)', round(max(ys) - min(ys), 4))
    pl.export(obj, 'fist', {'Ice': {'emissive': [0.1, 0.19, 0.36]}})


main()
