"""Bat storm (D-36): a ring storm of Xeen bats as one skinned decoration model with one seamless loop.

blender --background --factory-startup --python build_storm.py -- <xeen_bat.glb> <tex dir> <out.glb>   (also writes <out>_static.glb, the rigid rest copy)

The installed bat's LOD0 (3,537 triangles, skinned to Bat_Rig; the importer drops the LOD meshes) is collapse-decimated to about 250, its ears and legs
folded onto the head and spine; 24 copies stand in three rings around the origin (asset space, metres x 1.55 so one
bat's span is 1.55 m = the actor's 155 units at decoration height scale 100). One clip `storm`, LOOP seconds: every
bat beats its wings with the bat's own Fly clip, time-warped to a whole number of beats per loop, and circles its ring
a whole number of turns, bobbing a whole number of times, so the last frame meets the first.
"""
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, TEX, OUT = argv[0], Path(argv[1]), argv[2]

LOOP = 12.0            # seconds
FPS = 30
SPAN_SCALE = 1.55      # bat model span 1 m -> 1.55 m
TARGET_TRIS = 250
# rings: count, radius m, base height m, turns per loop (sign = direction), beats per loop, bob cycles, bank deg
RINGS = [
    (7, 7.0, 0.0, 2, 17, 3, 24),
    (8, 10.0, 2.6, -1, 16, 2, 18),
    (9, 13.0, 5.0, 1, 15, 2, 14),
]
DROP = {'Ear_L': 'Head', 'Ear_R': 'Head', 'Thigh_L': 'Spine1', 'Shin_L': 'Spine1', 'Thigh_R': 'Spine1',
        'Shin_R': 'Spine1'}
random.seed(36)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
scene = bpy.context.scene
scene.render.fps = FPS
src_arm = next(o for o in scene.objects if o.type == 'ARMATURE')
src_mesh = max((o for o in scene.objects if o.type == 'MESH' and 'Shadow' not in o.name), key=lambda o: len(o.data.polygons))
fly = bpy.data.actions['Fly'] if 'Fly' in bpy.data.actions else next(a for a in bpy.data.actions if a.name.startswith('Fly'))
for o in list(scene.objects):
    if o not in (src_arm, src_mesh):
        bpy.data.objects.remove(o, do_unlink=True)

# --- the reduced bat: decimate, fold dropped bones, one material with the baked colour --------------------------
bpy.context.view_layer.objects.active = src_mesh
for o in scene.objects:
    o.select_set(o == src_mesh)
mesh = src_mesh.data
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
mod = src_mesh.modifiers.new('dec', 'DECIMATE')
mod.ratio = TARGET_TRIS / tris
mod.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='dec')
groups = {g.name: g for g in src_mesh.vertex_groups}
for gone, keep in DROP.items():
    if gone in groups:
        g_gone, g_keep = groups[gone], groups[keep]
        for v in mesh.vertices:
            for ge in v.groups:
                if ge.group == g_gone.index and ge.weight > 0:
                    g_keep.add([v.index], ge.weight, 'ADD')
        src_mesh.vertex_groups.remove(g_gone)
mesh.materials.clear()
mat = bpy.data.materials.new('BatStorm')
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
img = nodes.new('ShaderNodeTexImage'); img.image = bpy.data.images.load(str(TEX / 'batstorm_basecolor.png'))
links.new(img.outputs['Color'], bsdf.inputs['Base Color'])
nimg = nodes.new('ShaderNodeTexImage'); nimg.image = bpy.data.images.load(str(TEX / 'batstorm_normal.png'))
nimg.image.colorspace_settings.name = 'Non-Color'
nmap = nodes.new('ShaderNodeNormalMap')
links.new(nimg.outputs['Color'], nmap.inputs['Color']); links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
bsdf.inputs['Roughness'].default_value = 0.8
bsdf.inputs['Metallic'].default_value = 0.0
# Blended (alpha just under 1): the runtime and the outdoor bake cast no shadow from blended materials.
bsdf.inputs['Alpha'].default_value = 0.98
for attr, value in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
    try:
        setattr(mat, attr, value)
    except (AttributeError, TypeError):
        pass
mat.use_backface_culling = False
mesh.materials.append(mat)
bat_tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print('BAT tris', bat_tris, 'groups', len(src_mesh.vertex_groups))

# --- source rest and the Fly curves --------------------------------------------------------------------------
bones = [b.name for b in src_arm.data.bones if b.name not in DROP]
W = src_arm.matrix_world.copy()
rest = {b.name: W @ b.matrix_local for b in src_arm.data.bones}
roots = [b.name for b in src_arm.data.bones if b.parent is None and b.name not in DROP]
assert roots == ['Spine1'], roots
head = rest['Head'].translation; spine = rest['Spine1'].translation
fwd = Vector((head.x - spine.x, head.y - spine.y, 0)).normalized()
up = Vector((0, 0, 1))
fly_start, fly_end = fly.frame_range


def curves(action):
    out = {}
    fcurves = action.fcurves if hasattr(action, 'fcurves') and len(action.fcurves) else None
    if fcurves is None:  # Blender 5 layered actions
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    fcurves = bag.fcurves
    for fc in fcurves:
        if not fc.data_path.startswith('pose.bones["'):
            continue
        name = fc.data_path.split('"')[1]
        prop = fc.data_path.rsplit('.', 1)[1]
        out[(name, prop, fc.array_index)] = fc
    return out


fly_curves = curves(fly)


def fly_basis(name, u):
    """The bone's matrix_basis in the Fly clip at cycle fraction u (0..1)."""
    frame = fly_start + (u % 1.0) * (fly_end - fly_start)
    get = lambda prop, i, d: fly_curves[(name, prop, i)].evaluate(frame) if (name, prop, i) in fly_curves else d
    loc = Vector([get('location', i, 0.0) for i in range(3)])
    quat = Quaternion([get('rotation_quaternion', i, 1.0 if i == 0 else 0.0) for i in range(4)]).normalized()
    scale = Vector([get('scale', i, 1.0) for i in range(3)])
    return loc, quat, scale


# --- the storm armature: one bone set per bat ----------------------------------------------------------------
bats = []
for ring, (count, radius, base_z, turns, beats, bobs, bank) in enumerate(RINGS):
    step = 2 * math.pi / count
    for i in range(count):
        bats.append(dict(ring=ring, angle=i * step + random.uniform(-0.3, 0.3) * step + ring * 0.7,
                         radius=radius + random.uniform(-0.6, 0.6), z=base_z + random.uniform(-0.5, 0.5),
                         turns=turns, beats=beats, bobs=bobs, bank=math.radians(bank + random.uniform(-5, 5)),
                         phase=random.random(), bob_phase=random.random(), bob_amp=random.uniform(0.25, 0.55)))

arm_data = bpy.data.armatures.new('BatStorm_Rig')
arm = bpy.data.objects.new('BatStorm_Rig', arm_data)
scene.collection.objects.link(arm)
S = Matrix.Scale(SPAN_SCALE, 4)


def placement(bat, t):
    """Armature-space matrix of the bat's frame at time t (orbit, bob, heading along the motion, bank inward)."""
    sign = 1 if bat['turns'] > 0 else -1
    a = bat['angle'] + 2 * math.pi * bat['turns'] * t / LOOP
    pos = Vector((bat['radius'] * math.cos(a), bat['radius'] * math.sin(a),
                  bat['z'] + bat['bob_amp'] * math.sin(2 * math.pi * (bat['bobs'] * t / LOOP + bat['bob_phase']))))
    tangent = Vector((-math.sin(a), math.cos(a), 0)) * sign
    heading = math.atan2(tangent.y, tangent.x) - math.atan2(fwd.y, fwd.x)
    roll = Matrix.Rotation(-bat['bank'] * sign, 4, Vector(fwd))  # wing toward the centre dips
    return Matrix.Translation(pos) @ Matrix.Rotation(heading, 4, 'Z') @ roll @ S


bpy.context.view_layer.objects.active = arm
for o in scene.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
src_edit = {b.name: (W @ b.head_local, W @ b.tail_local, b.parent.name if b.parent else None)
            for b in src_arm.data.bones}
roll_src = {}
for k, bat in enumerate(bats):
    place = placement(bat, 0.0)
    for name in bones:
        h, t, parent = src_edit[name]
        eb = arm_data.edit_bones.new(f'B{k:02d}_{name}')
        eb.head = place @ h
        eb.tail = place @ t
        eb.align_roll((place.to_3x3() @ (rest[name].to_3x3() @ Vector((0, 0, 1)))))
        if parent:
            eb.parent = arm_data.edit_bones[f'B{k:02d}_{parent}']
bpy.ops.object.mode_set(mode='OBJECT')

# Rest rotations differ slightly from the source (edit-bone roll rounding); carry poses through rest matrices.
new_rest = {b.name: b.matrix_local.copy() for b in arm_data.bones}

# --- the mesh: 24 copies, groups renamed per bat ------------------------------------------------------------
pieces = []
for k, bat in enumerate(bats):
    copy = src_mesh.copy(); copy.data = src_mesh.data.copy()
    scene.collection.objects.link(copy)
    copy.modifiers.clear(); copy.parent = None
    copy.matrix_world = Matrix.Identity(4)
    copy.data.transform(placement(bat, 0.0) @ src_mesh.matrix_world)
    for g in copy.vertex_groups:
        g.name = f'B{k:02d}_{g.name}'
    pieces.append(copy)
for o in scene.objects:
    o.select_set(o in pieces)
bpy.context.view_layer.objects.active = pieces[0]
bpy.ops.object.join()
storm = pieces[0]; storm.name = 'BatStorm'; storm.data.name = 'BatStorm'
storm.parent = arm
storm.modifiers.new('arm', 'ARMATURE').object = arm
bpy.data.objects.remove(src_mesh, do_unlink=True)
print('STORM tris', sum(len(p.vertices) - 2 for p in storm.data.polygons), 'bats', len(bats),
      'bones', len(arm_data.bones))

# --- the clip -------------------------------------------------------------------------------------------------
action = bpy.data.actions.new('storm')
arm.animation_data_create(); arm.animation_data.action = action
frames = int(round(LOOP * FPS))
pose = arm.pose
for pb in pose.bones:
    pb.rotation_mode = 'QUATERNION'
order = [b.name for b in src_arm.data.bones if b.name in bones]  # parents before children


def rigid(m):
    loc, rot, _ = m.decompose()
    return Matrix.LocRotScale(loc, rot, None)


rel_rest = {}
for name in bones:
    parent = src_edit[name][2]
    rel_rest[name] = rest[parent].inverted() @ rest[name] if parent else None
for f in range(frames + 1):
    t = f / FPS
    for k, bat in enumerate(bats):
        u = bat['beats'] * t / LOOP + bat['phase']
        place = placement(bat, t)
        src_posed, posed = {}, {}
        for name in order:
            loc, quat, _ = fly_basis(name, u)
            basis_src = Matrix.LocRotScale(loc, quat, None)
            parent = src_edit[name][2]
            src_posed[name] = (src_posed[parent] @ rel_rest[name] if parent else rest[name]) @ basis_src
            posed[name] = rigid(place @ src_posed[name])
        for name in order:
            pb = pose.bones[f'B{k:02d}_{name}']
            parent = src_edit[name][2]
            if parent is None:
                basis = new_rest[pb.name].inverted() @ posed[name]
            else:
                pn = f'B{k:02d}_{parent}'
                basis = (new_rest[pn].inverted() @ new_rest[pb.name]).inverted() @ posed[parent].inverted() @ posed[name]
            l, q, _ = basis.decompose()
            pb.location = l; pb.rotation_quaternion = q
            pb.keyframe_insert('location', frame=f); pb.keyframe_insert('rotation_quaternion', frame=f)
scene.frame_start, scene.frame_end = 0, frames
print('CLIP frames', frames + 1, 'seconds', LOOP)

# Only the storm's own material and clip go out (the import's variants, materials and clips stay behind).
storm.data.materials.clear()
storm.data.materials.append(mat)
for poly in storm.data.polygons:
    poly.material_index = 0
if hasattr(storm.data, 'gltf_variant_mesh_data'):
    storm.data.gltf_variant_mesh_data.clear()
for other in list(bpy.data.actions):
    if other != action:
        bpy.data.actions.remove(other)
for other in list(bpy.data.materials):
    if other != mat:
        bpy.data.materials.remove(other)
for holder in (scene, storm.data):
    for key in [k for k in dir(holder) if 'variant' in k.lower()]:
        value = getattr(holder, key)
        print('VARIANT_PROP', type(holder).__name__, key, type(value).__name__)
        if hasattr(value, 'clear'):
            value.clear()
print('MATS', [m.name if m else None for m in storm.data.materials], mat.name, len(bpy.data.materials))
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True); storm.select_set(True)
options = dict(filepath=OUT, export_format='GLB', use_selection=True, export_animations=True,
               export_animation_mode='ACTIONS', export_skins=True, export_yup=True, export_force_sampling=True,
               export_frame_range=False, export_apply=False)
if 'export_gltf_variants' in bpy.ops.export_scene.gltf.get_rna_type().properties:
    options['export_gltf_variants'] = False
bpy.ops.export_scene.gltf(**options)
print('EXPORTED', OUT)

# The binding's static model (picking only, never drawn; decoration models must be rigid): the storm at rest.
storm.modifiers.clear()
storm.parent = None
storm.matrix_world = Matrix.Identity(4)
storm.vertex_groups.clear()
bpy.data.objects.remove(arm, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
storm.select_set(True)
static_out = OUT.replace('.glb', '_static.glb')
options.update(filepath=static_out, export_animations=False, export_skins=False)
bpy.ops.export_scene.gltf(**options)
print('EXPORTED', static_out)
