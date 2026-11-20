"""Core figure of the MM6 fire elemental (fie1): a slim, featureless MPFB2 body on the MPFB Mixamo rig. Run under
Blender:

    blender --background --factory-startup --python scripts/build_figure.py

The restored sprites show a dark-red human shape without face, fingers or clothes inside the flame cage, so the
MakeHuman base mesh is enough (no Meshy): helper geometry removed, the face, ears and hands smoothed into soft
shapes, decimated to the triangle budget with its MPFB rig weights kept.

Units: 1 Blender unit = 100 native logical pixels, origin at the sprite's ground pivot, forward -Y (as aie1). The
restored standing and attack frames put the figure's feet about 0.2 above the pivot and the head top at about 2.05
(fie1ata0/atc0, 2x pixels 110..480 of a 520-row canvas). The feet sit a little higher (0.36) so the hanging legs
stay inside the narrowing cage; the 1.6-unit MPFB body is scaled to 1.66 and lifted.
Writes work/figure.blend (FireElemental_Body + FireElemental_Rig, Mixamo bone names without the prefix).
"""
import math
import os

import addon_utils
import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MACROS = {'gender': 0.5, 'age': 0.5, 'muscle': 0.45, 'weight': 0.15, 'proportions': 0.9, 'height': 0.5,
          'cupsize': 0.2, 'firmness': 0.5, 'race': {'asian': 0.0, 'caucasian': 1.0, 'african': 0.0}}
FIGURE_BOTTOM = 0.36
FIGURE_TOP = 2.02
TARGET_TRIANGLES = 3000
# MPFB's A-pose holds the hands about 0.52 out at 1.42 high, at the cage's edge; the sprite's arms hang lower (hands
# about 0.53 out at 1.25, inside the widest part of the cage). The rest pose drops them further (degrees).
ARM_DOWN = 18.0
FOREARM_DOWN = 10.0
# The sprite's legs hang together into the cage's lower point.
LEG_IN = 4.0
# Laplacian passes that melt the face, ears, fingers and toes into soft shapes (vertex weight on these bones).
SMOOTH = [('Head', 0.5, 12), ('Hand', 0.3, 10), ('Foot', 0.3, 6), ('ToeBase', 0.3, 6)]


def clear():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def bake_shape(human):
    human.shape_key_add(name='baked', from_mix=True)
    baked = [tuple(k.co) for k in human.data.shape_keys.key_blocks['baked'].data]
    human.shape_key_clear()
    for vertex, co in zip(human.data.vertices, baked):
        vertex.co = co


def keep_body(human):
    """Delete helper geometry (eyes, teeth, joint cubes, clothing helpers): only the 'body' group stays."""
    body = human.vertex_groups['body'].index
    bm = bmesh.new()
    bm.from_mesh(human.data)
    deform = bm.verts.layers.deform.active
    remove = [v for v in bm.verts if v[deform].get(body, 0.0) <= 0.0]
    bmesh.ops.delete(bm, geom=remove, context='VERTS')
    bm.to_mesh(human.data)
    bm.free()
    for modifier in [m for m in human.modifiers if m.type == 'MASK']:
        human.modifiers.remove(modifier)
    for group in [g for g in human.vertex_groups if not g.name.startswith('mixamorig:')]:
        human.vertex_groups.remove(group)


def smooth_regions(human):
    """Weighted Laplacian smoothing per region: a vertex moves toward its neighbours' mean by its weight on the
    region's bones (both sides, all descendants such as fingers)."""
    mesh = human.data
    neighbours = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        neighbours[a].append(b)
        neighbours[b].append(a)
    for suffix, threshold, passes in SMOOTH:
        groups = {g.index for g in human.vertex_groups
                  if g.name.endswith(suffix) or (suffix == 'Hand' and 'Hand' in g.name)}
        strength = []
        for vertex in mesh.vertices:
            total = sum(g.weight for g in vertex.groups if g.group in groups)
            strength.append(min(1.0, max(0.0, (total - threshold) / (1.0 - threshold)) * 1.5))
        for _ in range(passes):
            positions = [v.co.copy() for v in mesh.vertices]
            for vertex in mesh.vertices:
                s = strength[vertex.index]
                if s <= 0.0 or not neighbours[vertex.index]:
                    continue
                mean = sum((positions[n] for n in neighbours[vertex.index]), Vector()) / len(neighbours[vertex.index])
                vertex.co = positions[vertex.index].lerp(mean, 0.6 * s)


def lower_arms(human, rig):
    """Pose the arms down and the legs together, apply the pose to the mesh and make it the rest pose."""
    def rotate_world(pb, degrees):
        head = pb.head.copy()
        turn = Matrix.Translation(head) @ Matrix.Rotation(math.radians(degrees), 4, 'Y') @ Matrix.Translation(-head)
        pb.matrix = turn @ pb.matrix
        bpy.context.view_layer.update()

    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    for side, sign in (('Left', 1.0), ('Right', -1.0)):
        rotate_world(rig.pose.bones[f'mixamorig:{side}Arm'], sign * ARM_DOWN)
        rotate_world(rig.pose.bones[f'mixamorig:{side}ForeArm'], sign * FOREARM_DOWN)
        rotate_world(rig.pose.bones[f'mixamorig:{side}UpLeg'], -sign * LEG_IN)
    bpy.ops.object.mode_set(mode='OBJECT')
    modifier = next(m for m in human.modifiers if m.type == 'ARMATURE')
    bpy.context.view_layer.objects.active = human
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    modifier = human.modifiers.new('Armature', 'ARMATURE')
    modifier.object = rig


def decimate(human):
    triangles = sum(len(p.vertices) - 2 for p in human.data.polygons)
    modifier = human.modifiers.new('Decimate', 'DECIMATE')
    modifier.ratio = TARGET_TRIANGLES / triangles
    modifier.use_symmetry = True
    modifier.symmetry_axis = 'X'
    bpy.context.view_layer.objects.active = human
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode='OBJECT')
    for polygon in human.data.polygons:
        polygon.use_smooth = True


def main():
    addon_utils.enable('bl_ext.blender_org.mpfb', default_set=True)
    from bl_ext.blender_org.mpfb.services.humanservice import HumanService
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable('bl_ext.blender_org.mpfb', default_set=True)
    clear()
    human = HumanService.create_human(macro_detail_dict=MACROS, feet_on_ground=True, scale=0.1)
    rig = HumanService.add_builtin_rig(human, 'mixamo')
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = human
    bake_shape(human)
    keep_body(human)
    smooth_regions(human)
    lower_arms(human, rig)
    # Drop the proxy-weight helpers MPFB leaves (none expected) and any material slots.
    human.data.materials.clear()
    decimate(human)
    # Rename bones and groups without the Mixamo prefix (shorter glTF names; actors.yml uses them).
    for bone in rig.data.bones:
        bone.name = bone.name.replace('mixamorig:', '')
    for group in human.vertex_groups:
        group.name = group.name.replace('mixamorig:', '')
    human.name, human.data.name = 'FireElemental_Body', 'FireElemental_Body'
    rig.name, rig.data.name = 'FireElemental_Rig', 'FireElemental_Rig'
    # Scale and lift onto the sprite's figure: apply to rig and mesh so the rest pose is in final units.
    bpy.context.view_layer.update()
    zs = [human.matrix_world @ v.co for v in human.data.vertices]
    low, high = min(p.z for p in zs), max(p.z for p in zs)
    scale = (FIGURE_TOP - FIGURE_BOTTOM) / (high - low)
    rig.scale = (scale, scale, scale)
    rig.location = (0.0, 0.0, FIGURE_BOTTOM - low * scale)
    bpy.context.view_layer.update()
    for obj in (rig, human):
        obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    human.select_set(True)
    bpy.context.view_layer.objects.active = human
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'figure.blend'))
    zs = [v.co.z for v in human.data.vertices]
    print('FIGURE', len(human.data.polygons), 'triangles', len(human.data.vertices), 'vertices, z', round(min(zs), 3),
          round(max(zs), 3), 'bones', len(rig.data.bones))


main()
