"""MM8 Fire Elemental figure: effect-body MPFB exception from the shared non-humanoid playbook.
Bald muscular fire figure and open hands; no clothing or equipment.
Native figure height establishes final units, forward -Y.
"""
import math
import numpy as np
import os

import addon_utils
import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MACROS = {'gender': 1.0, 'age': 0.5, 'muscle': 1.0, 'weight': 0.62, 'proportions': 0.9, 'height': 0.5,
          'cupsize': 0.2, 'firmness': 0.5, 'race': {'asian': 0.0, 'caucasian': 1.0, 'african': 0.0}}
FIGURE_BOTTOM = 0.10
FIGURE_TOP = 1.95
TARGET_TRIANGLES = 6400
# MPFB's A-pose holds the hands about 0.52 out at 1.42 high, at the torso silhouette; the sprite's arms hang lower (hands
# about 0.53 out at 1.25, beside the vortex waist). The rest pose drops them further (degrees).
ARM_DOWN = 8.0
FOREARM_DOWN = 5.0
# Close the legs slightly before adding the floating pose.
LEG_IN = 4.0
# Soften face, ears and fingers using their bone weights.
SMOOTH = [('Head', 0.5, 2), ('Hand', 0.3, 2)]


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
    from bl_ext.blender_org.mpfb.services.targetservice import TargetService
    targets = {'torso/torso-muscle-pectoral-incr': 1.0, 'torso/torso-muscle-dorsi-incr': 0.85,
               'torso/torso-vshape-incr': 0.45, 'torso/torso-scale-depth-incr': 0.25,
               'neck/measure-neck-circ-incr': 0.35, 'stomach/stomach-tone-incr': 1.0}
    for side in ['l', 'r']:
        for target, amount in [('upperarm-muscle-incr', 1.0), ('upperarm-shoulder-muscle-incr', 1.0),
                               ('lowerarm-muscle-incr', 1.0), ('upperarm-scale-horiz-incr', 0.35),
                               ('upperarm-scale-depth-incr', 0.35), ('lowerarm-scale-horiz-incr', 0.25),
                               ('lowerarm-scale-depth-incr', 0.25)]:
            targets['arms/' + side + '-' + target] = amount
    for name, value in targets.items():
        path = TargetService.target_full_path(name.rsplit('/', 1)[-1])
        assert path, name
        TargetService.load_target(human, path, weight=value)
    bpy.context.view_layer.update()
    rig = HumanService.add_builtin_rig(human, 'mixamo')
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = human
    bake_shape(human)
    keep_body(human)
    smooth_regions(human)
    lower_arms(human, rig)
    # Drop the proxy-weight helpers MPFB leaves (none expected) and any material slots.
    human.data.materials.clear()
    # Rename bones and groups without the Mixamo prefix (shorter glTF names; actors.yml uses them).
    for bone in rig.data.bones:
        bone.name = bone.name.replace('mixamorig:', '')
    for group in human.vertex_groups:
        group.name = group.name.replace('mixamorig:', '')
    bm=bmesh.new();bm.from_mesh(human.data)
    head_z=rig.data.bones['Head'].head_local.z
    eye_edges=[e for e in bm.edges if e.is_boundary and all(v.co.z>head_z for v in e.verts)]
    if eye_edges:bmesh.ops.holes_fill(bm,edges=eye_edges,sides=0)
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(human.data);bm.free()
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
    # The restored front view has three paired abdominal masses, with clear separation under the pectorals.
    for vertex in human.data.vertices:
        x, y, z = vertex.co
        front = max(0.0, min(1.0, -y / 0.08))
        if front > 0 and abs(x) < 0.22 and 1.28 < z < 1.64:
            relief = sum(0.025 * math.exp(-((abs(x) - 0.052) / 0.039) ** 2
                                         - ((z - row) / 0.035) ** 2)
                         for row in [1.34, 1.43, 1.52])
            vertex.co.y -= front * relief
    human.data.update()
    # Remove the sharp rest-pose scapula fold before reducing the sculpted torso.
    mesh=human.data;neighbours=[[] for v in mesh.vertices]
    for edge in mesh.edges:
        a,b=edge.vertices;neighbours[a].append(b);neighbours[b].append(a)
    for iteration in range(4):
        positions=[v.co.copy() for v in mesh.vertices]
        for vertex in mesh.vertices:
            x,y,z=vertex.co
            strength=.5*math.exp(-((abs(x)-.16)/.10)**2-((z-1.73)/.10)**2)*max(0,min(1,y/.06))
            if strength>.01 and neighbours[vertex.index]:
                mean=sum((positions[i] for i in neighbours[vertex.index]),Vector())/len(neighbours[vertex.index])
                vertex.co=positions[vertex.index].lerp(mean,strength)
    decimate(human)
    # MPFB's abrupt axilla weights stretch in the forward cast; diffuse them along the actual shoulder surface.
    mesh=human.data;weights=np.zeros((len(mesh.vertices),len(human.vertex_groups)))
    for vertex in mesh.vertices:
        for g in vertex.groups:weights[vertex.index,g.group]=g.weight
    neighbours=[[] for v in mesh.vertices]
    for edge in mesh.edges:
        a,b=edge.vertices;neighbours[a].append(b);neighbours[b].append(a)
    for iteration in range(12):
        old=weights.copy()
        for vertex in mesh.vertices:
            x,y,z=vertex.co;strength=.55*math.exp(-((abs(x)-.235)/.13)**2-((z-1.65)/.16)**2)
            if strength>.025 and neighbours[vertex.index]:weights[vertex.index]=(1-strength)*old[vertex.index]+strength*old[neighbours[vertex.index]].mean(0)
    for group in human.vertex_groups:
        group.remove(list(range(len(mesh.vertices))))
        for index,weight in enumerate(weights[:,group.index]):
            if weight>1e-5:group.add([index],float(weight),'REPLACE')
    bpy.context.view_layer.objects.active=human
    bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    assert all(sum(g.weight for g in v.groups)>0.99 for v in human.data.vertices)
    for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
    os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'figure.blend'))
    zs = [v.co.z for v in human.data.vertices]
    print('FIGURE', len(human.data.polygons), 'triangles', len(human.data.vertices), 'vertices, z', round(min(zs), 3),
          round(max(zs), 3), 'bones', len(rig.data.bones))


main()
