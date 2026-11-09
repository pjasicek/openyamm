"""Export the corrected master, check preservation, and render the actual returned GLB."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

stage = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('material_author', stage / 'author_materials.py')
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
bpy.ops.wm.open_mainfile(filepath=str(stage / 'authored_checkpoint.blend'))
source = bpy.data.scenes[author.SCENE]
bpy.context.window.scene = source
mesh = next(o for o in source.objects if o.get('material_role') == 'body')
rig = next(o for o in source.objects if o.get('material_role') == 'rig')
baseline = bpy.data.scenes['MM6_Demon_Native_Animations']
old_mesh = next(o for o in baseline.objects if o.name.startswith('Demon_Native_Mesh'))
old_rig = next(o for o in baseline.objects if o.type == 'ARMATURE')


def vertices(obj):
    return np.array([v.co for v in obj.data.vertices])


def curves(action):
    return {(c.data_path, c.array_index): [(tuple(k.co), k.interpolation) for k in c.keyframe_points]
            for c in action.layers[0].strips[0].channelbag(action.slots[0]).fcurves}


assert np.array_equal(vertices(mesh), vertices(old_mesh))
assert [tuple(p.vertices) for p in mesh.data.polygons] == [tuple(p.vertices) for p in old_mesh.data.polygons]
assert np.array_equal(np.array([u.uv for u in mesh.data.uv_layers[0].data]),
                      np.array([u.uv for u in old_mesh.data.uv_layers[0].data]))
assert [g.name for g in mesh.vertex_groups] == [g.name for g in old_mesh.vertex_groups]
assert [[(g.group, g.weight) for g in v.groups] for v in mesh.data.vertices] == \
       [[(g.group, g.weight) for g in v.groups] for v in old_mesh.data.vertices]
assert np.array_equal(np.array([n.vector for n in mesh.data.corner_normals]),
                      np.array([n.vector for n in old_mesh.data.corner_normals]))
assert all(np.array_equal(np.array(b.matrix_local), np.array(old_rig.data.bones[b.name].matrix_local))
           for b in rig.data.bones)
clips = {t.name: t.strips[0] for t in rig.animation_data.nla_tracks}
old_clips = {t.name: t.strips[0] for t in old_rig.animation_data.nla_tracks}
assert len(clips) == 9 and clips.keys() == old_clips.keys()
for name, strip in clips.items():
    assert curves(strip.action) == curves(old_clips[name].action), name
    assert (strip.frame_start, strip.frame_end) == (old_clips[name].frame_start, old_clips[name].frame_end)
regions = json.loads((stage / 'material_regions.json').read_text())
indices = {int(i) for i in regions['claw_faces']}
for a, b in zip(mesh.data.polygons, old_mesh.data.polygons):
    assert a.material_index == (3 if a.index in indices else b.material_index)
print('Geometry, UVs, normals, weights, bind and all nine animation curves preserved.', flush=True)

# The normalizer uses canonical effect-node names. Rename only inside this background export process.
for obj in source.objects:
    canonical = obj.name.removeprefix('Textured_')
    if canonical in bpy.data.objects:
        bpy.data.objects[canonical].name = 'Preserved_' + canonical
    obj.name = canonical
rotations = {'mixamorig:'+s+p: [] for s in ('Right', 'Left') for p in ('UpLeg', 'Leg', 'Foot')}
for sample in range(129):
    author.select(source, 'Running', sample/4)
    for name, rows in rotations.items():
        bone = rig.pose.bones[name]
        q = (bone.parent.matrix.inverted() @ bone.matrix).to_quaternion()
        row = [q.x, q.y, q.z, q.w]
        if rows and sum(a*b for a, b in zip(row, rows[-1])) < 0:
            row = [-v for v in row]
        rows.append(row)
death = []
for frame in range(61):
    author.select(source, 'Death', frame)
    death.append([k.value for k in source.objects['Demon_Death_Plume'].data.shape_keys.key_blocks][1:])
author.select(source, 'Standing', 0)
matrices = {obj: obj.matrix_basis.copy() for obj in source.objects}
for obj in source.objects:
    obj.hide_set(False)
    obj.select_set(obj.type != 'CAMERA')
    for owner in (obj, obj.data.shape_keys if obj.type == 'MESH' else None):
        if owner is not None and owner.animation_data:
            owner.animation_data.action = None
            for track in owner.animation_data.nla_tracks:
                track.mute = True
bpy.context.view_layer.objects.active = rig
output_glb = stage / 'mm6_demon_textured.glb'
bpy.ops.export_scene.gltf(filepath=str(output_glb), export_format='GLB', use_selection=True,
    use_active_scene=True, export_animations=True, export_animation_mode='NLA_TRACKS',
    export_frame_range=False, export_force_sampling=True, export_frame_step=1, export_all_influences=True,
    export_def_bones=False, export_optimize_animation_size=False, export_materials='EXPORT',
    export_normals=True, export_yup=True, export_cameras=False, export_lights=False,
    export_morph=True, export_morph_animation=True, export_image_format='AUTO')
spec = importlib.util.spec_from_file_location('normalize_export', stage.parent / 'animations_native_v7_20261005/normalize_export.py')
normalizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normalizer)
normalizer.normalize(output_glb, death, rotations)
for obj, matrix in matrices.items():
    obj.matrix_basis = matrix
author.select(source, 'Standing', 0)
rig.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'mm6_demon_textured.blend'), compress=True)

actual = bpy.data.scenes.new('MM6_Demon_Actual_Textured_Export')
bpy.context.window.scene = actual
actual.render.fps = 48
bpy.ops.import_scene.gltf(filepath=str(output_glb))
imported = next(o for o in actual.objects if o.type == 'MESH' and o.name.startswith('Demon_Native_Mesh'))
assert len(imported.data.polygons) == 16474
tree = KDTree(len(mesh.data.vertices))
for v in mesh.data.vertices:
    tree.insert(v.co, v.index)
tree.balance()
matches = [tree.find(v.co) for v in imported.data.vertices]
rest_error = max(item[2] for item in matches)
worst = max(range(len(matches)), key=lambda i: matches[i][2])
# Blender reconstructs skinned rest coordinates through float32 inverse-bind matrices.
# Use the established revision-7 import tolerance; the authored data remain exactly unchanged.
assert rest_error < 1e-5, (rest_error, tuple(imported.data.vertices[worst].co),
                          tuple(mesh.data.vertices[matches[worst][1]].co),
                          vertices(imported).min(0).tolist(), vertices(imported).max(0).tolist())
mapping = [item[1] for item in matches]


def evaluated(scene, obj):
    bpy.context.window.scene = scene
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    temporary = evaluated.to_mesh()
    points = np.array([v.co for v in temporary.vertices])
    matrix = np.array(evaluated.matrix_world)
    evaluated.to_mesh_clear()
    return points @ matrix[:3, :3].T + matrix[:3, 3]


pose_errors = {}
for clip, frame in [('Standing', 0), ('Walk_Native', 15), ('Attack', 12), ('Attack', 24), ('Hit', 18),
                    ('Fidget', 18), ('Walking', 25), ('Running', 16.25), ('Death', 12), ('Ash_Remains', 0)]:
    author.select(source, clip, frame)
    expected = evaluated(source, mesh)
    author.select(actual, clip, frame)
    found = evaluated(actual, imported)
    error = float(np.abs(expected[mapping]-found).max())
    assert error < 4e-6, (clip, frame, error)
    pose_errors[f'{clip}:{frame}'] = error
print('Actual animated GLB round-trip checks passed.', pose_errors, flush=True)

raw = output_glb.read_bytes()
size = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20+size])
assert len(doc['skins'][0]['joints']) == 85
assert {a['name'] for a in doc['animations']} == set(clips)
material_by_name = {m['name']: m for m in doc['materials']}
for name, rgb in [('Demon_Red_Iris', (.86, .38, .36)),
                  ('Demon_Black_Pupil', (.015, .012, .012))]:
    pbr = material_by_name[name]['pbrMetallicRoughness']
    assert np.allclose(pbr['baseColorFactor'], author.srgb(rgb), atol=1e-7)
    assert pbr['metallicFactor'] == 0
    assert 'baseColorTexture' not in pbr
claw_pbr = material_by_name['Demon_White_Claws']['pbrMetallicRoughness']
assert 'baseColorTexture' in claw_pbr and claw_pbr['metallicFactor'] == 0
assert 'normalTexture' in material_by_name['Demon_White_Claws']
assert 'normalTexture' not in material_by_name['Demon_Red_Iris']
assert 'normalTexture' not in material_by_name['Demon_Black_Pupil']

actual.render.engine = source.render.engine
actual.render.resolution_percentage = 100
actual.render.image_settings.file_format = 'PNG'
actual.view_settings.view_transform = source.view_settings.view_transform
world = bpy.data.worlds.new('Demon_Review_Neutral_World')
world.use_nodes = True
background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
background.inputs['Color'].default_value = (.055, .055, .055, 1)
background.inputs['Strength'].default_value = .8
actual.world = world
camera = bpy.data.objects.new('Material_Review_Camera', bpy.data.cameras.new('Material_Review_Camera'))
actual.collection.objects.link(camera)
actual.camera = camera
camera.data.type = 'ORTHO'
for name, position, power in [('Key', (-3, -4, 4), 500), ('Fill', (3, -2, 3), 400), ('Rim', (0, 3, 3), 600)]:
    light = bpy.data.lights.new('Material_Review_'+name, 'AREA')
    light.energy = power
    light.shape = 'DISK'
    light.size = 4
    obj = bpy.data.objects.new(light.name, light)
    actual.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector((0, 0, .9))-obj.location).to_track_quat('-Z', 'Y').to_euler()
frames = stage / 'review_frames'
frames.mkdir(exist_ok=True)
rendered = []


def render(name, center, direction, scale, dimensions=(900, 900)):
    bpy.context.window.scene = actual
    center, direction = Vector(center), Vector(direction)
    camera.location = center + direction
    camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = scale
    actual.render.resolution_x, actual.render.resolution_y = dimensions
    actual.render.filepath = str(frames / (name+'.png'))
    bpy.ops.render.render(write_still=True)
    rendered.append(name+'.png')


author.select(actual, 'Standing', 0)
features = [('face_front', (0, -.3, 1.56), (0, -6, 0), .47),
            ('face_left', (0, -.3, 1.56), (-3, -6, .1), .47),
            ('face_right', (0, -.3, 1.56), (3, -6, .1), .47),
            ('hands', (0, -.1, .63), (0, -6, 0), 1.7),
            ('feet_front', (0, -.07, .14), (0, -6, .3), 1.25),
            ('feet_profile', (0, -.07, .14), (-6, 0, .3), 1.25)]
author.select(source, 'Standing', 0)
standing = evaluated(source, mesh)
tips = json.loads((stage.parent / 'animations_native_v7_20261005/tip_vertex_masks.json').read_text())
for side in ('Right', 'Left'):
    points = standing[[i for label, ids in tips.items() if label.startswith(side+'_') for i in ids]]
    lo, hi = points.min(0), points.max(0)
    center = (lo+hi)/2 + np.array([0, 0, .035])
    scale = float(max(hi[0]-lo[0], hi[2]-lo[2]) * 1.5)
    features.append((side.lower()+'_hand', tuple(center), (0, -6, .1), scale))
original = mesh.data.materials[0]
slots = [s.material for s in imported.material_slots]
for prefix in ('after', 'before'):
    for slot, material in zip(imported.material_slots, slots):
        slot.material = material if prefix == 'after' else original
    for name, center, direction, scale in features:
        render(prefix+'_'+name, center, direction, scale)
for slot, material in zip(imported.material_slots, slots):
    slot.material = material
for clip, frame in [('Standing', 0), ('Walk_Native', 15), ('Attack', 12), ('Attack', 24),
                    ('Hit', 18), ('Fidget', 18), ('Walking', 25), ('Running', 16), ('Death', 12),
                    ('Death', 30), ('Ash_Remains', 0)]:
    author.select(actual, clip, frame)
    for view, direction in [('front', (0, -6, 0)), ('profile', (-6, 0, 0))]:
        render(f'{clip}_{frame}_{view}', (0, 0, .85), direction, 2.05, (900, 1000))
    print('Rendered', clip, frame, flush=True)
author.select(actual, 'Standing', 0)
render('Standing_0_back', (0, 0, .85), (0, 6, 0), 2.05, (900, 1000))
report = {'passed': True, 'vertices': 8323, 'triangles': 16474, 'joints': 85,
          'geometry_uvs_normals_weights_bind_identical': True, 'all_nine_animation_curves_identical': True,
          'actual_glb_reimport': True, 'sampled_pose_errors': pose_errors,
          'imported_rest_coordinate_error': rest_error,
          'white_claws_and_red_black_eyes_exported': True, 'white_claw_normal_detail_retained': True,
          'smooth_eye_materials': True, 'rendered': rendered,
          'claw_pigment': 'Neutral baked luminance L + 3.2 L^2, capped at 0.90 linear; dark roots retained.',
          'source_glb_sha256': regions['source_sha256'],
          'delivery_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [output_glb, stage / 'mm6_demon_textured.blend']}}
(stage / 'validation.json').write_text(json.dumps(report, indent=2)+'\n')
print('Delivered and reviewed corrected materials.', flush=True)
