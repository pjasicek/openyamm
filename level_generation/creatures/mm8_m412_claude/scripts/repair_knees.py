"""Repair the fitted knee centres and restore bend rows lost to planar mesh reduction."""
import bpy
import bmesh
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/master_grounded_delivery.blend'))
scene = bpy.context.scene
body = bpy.data.objects['Body']
rig = bpy.data.objects['Rig']
legs = [f'B_{side}_{part}' for side in 'LR' for part in ('Thigh', 'Calf', 'Foot', 'Toe0')]
pieces = np.array([a.value for a in body.data.attributes['piece'].data])
feet = np.flatnonzero(np.isin(pieces, (5, 6)))

def sample_frame(frame):
    scene.frame_set(math.floor(frame), subframe=frame % 1)

def sole_height():
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    xyz = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', xyz)
    z = xyz.reshape(-1, 3)[:, 2]
    value = (float(z[feet].min()), float(z.min()))
    evaluated.to_mesh_clear()
    return value

# Retain source world rotations and the selected sole/contact profile on every action.
samples = {}
for action in bpy.data.actions:
    if action.name not in ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Fidget'):
        continue
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    rows = []
    for frame in np.arange(action.frame_range[0], action.frame_range[1] + .001, .25):
        sample_frame(float(frame))
        rows.append((float(frame), {n: rig.pose.bones[n].matrix.to_quaternion().copy() for n in legs},
                     rig.pose.bones['B_Pelvis'].location.copy(), sole_height()))
    samples[action.name] = rows
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis.identity()
bpy.context.view_layer.update()

# The generic joint proposal missed the bowed right trouser leg by 77 mm.
joints = {}
report = {'joint_fit': {}, 'triangles_before': sum(len(f.vertices)-2 for f in body.data.polygons)}
for side, sign in (('L', 1), ('R', -1)):
    old = rig.data.bones[f'B_{side}_Calf'].head_local.copy()
    bm = bmesh.new()
    bm.from_mesh(body.data)
    layer = bm.verts.layers.int['piece']
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[layer] != 2 or v.co.x * sign < .02], context='VERTS')
    cut = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                               plane_co=old, plane_no=(0, 0, 1))
    edges = [e for e in cut['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    assert edges and all(sum(v in e.verts for e in edges) == 2 for v in {v for e in edges for v in e.verts})
    centre = sum(((e.verts[0].co + e.verts[1].co) * .5 * e.calc_length() for e in edges), Vector())
    centre /= sum(e.calc_length() for e in edges)
    joints[side] = centre.copy()
    report['joint_fit'][side] = {'before': list(old), 'after': list(centre), 'delta_mm': (old-centre).length*1000}
    bm.free()
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for side, centre in joints.items():
    for part in ('Thigh', 'Calf'):
        bone = rig.data.edit_bones[f'B_{side}_{part}']
        direction = (bone.tail - bone.head).normalized()
        roll = bone.matrix.to_3x3().col[2].copy()
        if part == 'Thigh':
            bone.tail = centre
        else:
            bone.head = centre
        swing = direction.rotation_difference((bone.tail - bone.head).normalized())
        bone.align_roll(swing @ roll)
bpy.ops.object.mode_set(mode='OBJECT')
offsets = json.loads(scene['rig_offsets'])
for n in legs:
    rest = rig.data.bones[n].matrix_local.to_3x3()
    offsets[n]['q'] = list((rest @ Matrix(offsets[n]['R_src']).inverted()).to_quaternion())
scene['rig_offsets'] = json.dumps(offsets)

# Keep UVs and surface shape; split only trousers across the flexing knee band.
bm = bmesh.new()
bm.from_mesh(body.data)
layer = bm.verts.layers.int['piece']
for z in (.44, .48, .52, .56, .60, .64, .68, .72):
    faces = [f for f in bm.faces if all(v[layer] == 2 for v in f.verts)]
    edges = {e for f in faces for e in f.edges}
    verts = {v for f in faces for v in f.verts}
    bmesh.ops.bisect_plane(bm, geom=list(verts) + list(edges) + faces,
                           plane_co=(0, 0, z), plane_no=(0, 0, 1), dist=1e-6)
# Plane cuts can land beside an existing vertex: weld those submillimetre slivers locally.
bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v[layer] == 2 and .438 < v.co.z < .722], dist=.0015)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
assert all(f.calc_area() > 1e-7 for f in bm.faces if all(v[layer] == 2 for v in f.verts)), 'knee sliver'
for face in bm.faces:
    if all(v[layer] == 2 for v in face.verts):
        face.smooth = True
bm.to_mesh(body.data)
bm.free()
body.data.update()
pieces = np.array([a.value for a in body.data.attributes['piece'].data])
feet = np.flatnonzero(np.isin(pieces, (5, 6)))
for side, centre in joints.items():
    thigh, calf = (f'B_{side}_{part}' for part in ('Thigh', 'Calf'))
    ti, ci = body.vertex_groups[thigh].index, body.vertex_groups[calf].index
    axis = (rig.data.bones[thigh].head_local - rig.data.bones[calf].tail_local).normalized()
    for vertex in body.data.vertices:
        if pieces[vertex.index] != 2 or vertex.co.x * centre.x < 0:
            continue
        distance = (vertex.co - centre).dot(axis)
        if abs(distance) > .18:
            continue
        weights = {g.group: g.weight for g in vertex.groups}
        t, c = weights.get(ti, 0), weights.get(ci, 0)
        u = float(np.clip(.5 + distance / .25, 0, 1))
        fade = float(np.clip((.18 - abs(distance)) / .04, 0, 1))
        new_thigh = t * (1-fade) + (t+c) * u*u*(3-2*u) * fade
        body.vertex_groups[thigh].add([vertex.index], new_thigh, 'REPLACE')
        body.vertex_groups[calf].add([vertex.index], t+c-new_thigh, 'REPLACE')
# Drop numerical zero groups and enforce the runtime's four-influence contract.
for vertex in body.data.vertices:
    weights = sorted([(g.group, g.weight) for g in vertex.groups if g.weight > 1e-7], key=lambda g: -g[1])
    assert len(weights) <= 4, (vertex.index, weights)
    assert abs(sum(w for _, w in weights)-1) < 1e-5
    for group in list(vertex.groups):
        if group.weight <= 1e-7:
            body.vertex_groups[group.group].remove([vertex.index])

inverse_root = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
report['actions'] = {}
for name, rows in samples.items():
    action = bpy.data.actions[name]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    corrections = []
    errors = []
    for frame, rotations, root_location, floor in rows:
        sample_frame(frame)
        rig.pose.bones['B_Pelvis'].location = root_location
        bpy.context.view_layer.update()
        for n in legs:
            rig.pose.bones[n].location.zero()
        bpy.context.view_layer.update()
        for n in legs:
            bone = rig.pose.bones[n]
            matrix = rotations[n].to_matrix().to_4x4()
            matrix.translation = bone.head
            bone.matrix = matrix
            bpy.context.view_layer.update()
            bone.keyframe_insert('rotation_quaternion', frame=frame)
            # Local translation remains zero: fitted segment lengths own the chain.
            assert bone.location.length < 1e-4, (name, frame, n, list(bone.location))
            bone.location.zero()
        bpy.context.view_layer.update()
        sole, lowest = sole_height()
        dz = max(floor[0] - sole, floor[1] - lowest)
        root = rig.pose.bones['B_Pelvis']
        root.location = root_location + inverse_root @ Vector((0, 0, dz))
        root.keyframe_insert('location', frame=frame)
        bpy.context.view_layer.update()
        after_sole, after_lowest = sole_height()
        errors.append(max(0, floor[1]-after_lowest, floor[0]-after_sole))
        corrections.append(dz)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    if any(f'["{n}"]' in curve.data_path for n in legs + ['B_Pelvis']):
                        for key in curve.keyframe_points:
                            key.interpolation = 'LINEAR'
    assert max(errors) < 1e-5
    report['actions'][name] = {'samples': len(rows), 'floor_undershoot_mm': max(errors)*1000,
                               'root_adjustment_mm': [min(corrections)*1000, max(corrections)*1000]}
    print('KNEE_ACTION', name, report['actions'][name], flush=True)
report['triangles_after'] = sum(len(f.vertices)-2 for f in body.data.polygons)
assert report['triangles_after'] < 15000
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/master_knees.blend'))
(P / 'review/knee_fix/repair.json').write_text(json.dumps(report, indent=2) + '\n')
print('KNEE_REPAIR', report)
