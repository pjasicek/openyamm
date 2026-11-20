"""Fit source frames to m628's bones; rigid skeletal pieces and fitted five-digit hands."""
import bpy
import bmesh
import json
import math
import sys
from pathlib import Path
import numpy as np
from mathutils import Matrix, Vector, Quaternion

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/body_static.blend'))
body = bpy.data.objects['Body']
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
piece = np.array([x.value for x in me.attributes['piece'].data])
source = json.loads((P / 'work/source_rest.json').read_text())


def points(pid):
    return co[piece == pid]


def ends(pts, ref):
    centre = pts.mean(0)
    axis = np.linalg.svd(pts - centre, full_matrices=False)[2][0]
    t = (pts - centre) @ axis
    a = pts[t <= np.quantile(t, .06)].mean(0)
    b = pts[t >= np.quantile(t, .94)].mean(0)
    return (a, b) if np.linalg.norm(a-ref) < np.linalg.norm(b-ref) else (b, a)


def unit(v):
    length = np.linalg.norm(v)
    assert length > 1e-7
    return v / length


joints = {}
for sd, pid in [('L', 8), ('R', 7)]:
    hip, knee = ends(points(pid), np.array([0, .03, 1.05]))
    joints[f'B_{sd}_Thigh'] = hip
    joints[f'B_{sd}_Calf'] = knee
centre_x = float((joints['B_L_Thigh'][0] + joints['B_R_Thigh'][0]) / 2)
joints.update({
    'B_Pelvis': np.array([centre_x, .035, 1.035]),
    'B_Spine': np.array([centre_x, .04, 1.14]),
    'B_Spine1': np.array([centre_x, .075, 1.28]),
    'B_Spine2': np.array([centre_x, .075, 1.42]),
    'B_Neck': np.array([centre_x, .055, 1.52]),
    'B_Head': np.array([centre_x, .035, 1.59]),
})
shoulder, elbow = ends(points(19), np.array([.15, .04, 1.48]))
fore_elbow, wrist = ends(points(15), elbow)
joints['B_L_UpperArm'] = shoulder
joints['B_L_Forearm'] = (elbow + fore_elbow) / 2
joints['B_L_Hand'] = np.concatenate([points(i) for i in (89, 90, 91)]).mean(0)
# The long glove conceals the right elbow; reflect the exposed left joint, not the glove cuff.
for role in ('UpperArm', 'Forearm'):
    v = joints['B_L_' + role].copy(); v[0] = 2*centre_x - v[0]
    joints['B_R_' + role] = v
joints['B_R_Hand'] = np.array([-.440, -.080, 1.018])
for sd in ('L', 'R'):
    sh = joints[f'B_{sd}_UpperArm']
    joints[f'B_{sd}_Clavicle'] = np.array([centre_x + (sh[0]-centre_x)*.25, .06, 1.46])
ankle = points(35).mean(0)
joints['B_L_Foot'] = ankle
joints['B_L_Toe0'] = np.array([ankle[0], -.075, .035])
joints['B_R_Foot'] = np.array([2*centre_x-ankle[0], ankle[1], ankle[2]])
joints['B_R_Toe0'] = np.array([joints['B_R_Foot'][0], -.10, .03])


def chain(sd, index):
    names = [f'B_{sd}_Finger{index}']
    while True:
        children = [n for n, v in source.items() if v['parent'] == names[-1]]
        if not children:
            break
        assert len(children) == 1
        names.append(children[0])
    assert len(names) == 3
    return names


def line(pts, base, n=12):
    a, b = ends(pts, base)
    direction = unit(b-a)
    depth = (pts-a) @ direction
    values = []
    for t in np.linspace(0, float((b-a) @ direction), n):
        mask = abs(depth-t) < max(.004, np.ptp(depth)/(n+1))
        values.append(pts[mask].mean(0) if mask.any() else a + direction*t)
    values[0] = a; values[-1] = b
    return np.array(values)


def sample(poly, fractions):
    lengths = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    distance = np.r_[0, np.cumsum(lengths)]
    return np.array([[np.interp(f*distance[-1], distance, poly[:, axis]) for axis in range(3)]
                     for f in fractions])


finger_lines = {'L': {}, 'R': {}}
left_parts = {0: 36, 1: 20, 2: 21, 3: 22, 4: 33}
for finger, pid in left_parts.items():
    poly = line(points(pid), joints['B_L_Hand'])
    fractions = [0, .40, .73, 1] if finger == 0 else [.34, .64, .84, 1]
    finger_lines['L'][finger] = sample(poly, fractions)

# Right glove fingers separate by connectivity beyond the palm. Grow their bases along the mesh.
idx = np.where(piece == 5)[0]
edges = [tuple(e.vertices) for e in me.edges if piece[e.vertices[0]] == 5 and piece[e.vertices[1]] == 5]
direction = unit(co[idx].mean(0) - joints['B_R_Hand'])
depth = (co - joints['B_R_Hand']) @ direction


def components(vertices):
    allowed = set(vertices)
    adjacency = {i: [] for i in allowed}
    for a, b in edges:
        if a in allowed and b in allowed:
            adjacency[a].append(b); adjacency[b].append(a)
    result = []
    while allowed:
        pending = [next(iter(allowed))]; group = []
        while pending:
            v = pending.pop()
            if v not in allowed:
                continue
            allowed.remove(v); group.append(v); pending.extend(adjacency[v])
        if len(group) >= 6:
            result.append(np.array(group))
    return result


thumb = None
for threshold in np.linspace(.02, .11, 80):
    groups = components(idx[depth[idx] > threshold])
    if len(groups) >= 2:
        candidate = max(groups, key=lambda a: co[a, 0].mean())
        if len(candidate) < len(idx)*.3 and co[candidate, 0].mean() > -.47:
            thumb = candidate
            break
assert thumb is not None, 'Right thumb needs a revised mesh cut'
remaining = np.array([i for i in idx if i not in set(thumb)])
fingers = None
for threshold in np.linspace(.045, .15, 120):
    groups = components(remaining[depth[remaining] > threshold])
    if len(groups) == 4:
        fingers = sorted(groups, key=lambda a: -co[a, 0].mean())
        break
assert fingers is not None, 'Right glove did not split into four fingers'
right_masks = [thumb] + fingers
right_owner = {int(v): f for f,vertices in enumerate(right_masks) for v in vertices}
for finger, vertices in enumerate(right_masks):
    poly = line(co[vertices], joints['B_R_Hand'])
    # Extend the cut base into the palm to retain the proximal phalanx hidden by the web.
    extension = unit(poly[1]-poly[0]) * (.008 if finger == 0 else .012)
    poly[0] -= extension
    finger_lines['R'][finger] = sample(poly, [0, .46, .78, 1])

tips = {}
for sd in ('L', 'R'):
    for finger, poly in finger_lines[sd].items():
        names = chain(sd, finger)
        for name, location in zip(names, poly): joints[name] = location
        tips[names[-1]] = poly[-1]

order = []
def visit(name):
    order.append(name)
    for n, value in source.items():
        if value['parent'] == name: visit(n)
visit('B_Pelvis')
assert set(order) == set(joints), (set(order)-set(joints), set(joints)-set(order))


def basis(forward, across):
    forward = unit(forward)
    across = unit(across-forward*np.dot(forward, across))
    return np.column_stack([forward, across, np.cross(forward, across)])


swings, rotations = {}, {}
for name in order:
    ref = source[name]
    child = ref['child']
    rest = Matrix(ref['rot'])
    if name.endswith('_Hand'):
        sd = name[2]
        a = basis(joints[f'B_{sd}_Finger2']-joints[name],
                  joints[f'B_{sd}_Finger1']-joints[f'B_{sd}_Finger4'])
        b = basis(np.array(source[f'B_{sd}_Finger2']['head'])-source[name]['head'],
                  np.array(source[f'B_{sd}_Finger1']['head'])-source[f'B_{sd}_Finger4']['head'])
        q = Matrix((a @ b.T).tolist()).to_quaternion()
    elif 'Finger' in name:
        sd = name[2]
        qh = swings[f'B_{sd}_Hand']
        sseg = Vector(ref['seg']) if child else Vector(ref['head'])-Vector(source[ref['parent']]['head'])
        target = joints[child] if child else tips[name]
        q = (qh @ sseg).rotation_difference(Vector(target-joints[name])) @ qh
    elif child in joints:
        q = Vector(ref['seg']).rotation_difference(Vector(joints[child]-joints[name]))
    else:
        q = swings.get(ref['parent'], Quaternion())
    if name == 'B_Pelvis': q = Quaternion()
    swings[name] = q; rotations[name] = q.to_matrix() @ rest

ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for name in order:
    eb = ad.edit_bones.new(name); eb.head = joints[name]
    child = source[name]['child']; length = np.linalg.norm(joints[child]-joints[name]) if child in joints else .025
    eb.tail = eb.head + rotations[name].col[1]*length; eb.align_roll(rotations[name].col[2])
    parent = source[name]['parent']
    if parent in ad.edit_bones: eb.parent = ad.edit_bones[parent]
jaw = ad.edit_bones.new('Jaw'); jaw.head = json.loads(bpy.context.scene['jaw_pivot'])
jaw.tail = jaw.head + Vector((0, -.05, -.02)); jaw.parent = ad.edit_bones['B_Head']
bpy.ops.object.mode_set(mode='OBJECT')
errors = [math.degrees(rig.data.bones[n].matrix_local.to_quaternion().rotation_difference(
          rotations[n].to_quaternion()).angle) for n in order]
assert max(min(x, 360-x) for x in errors) < .1, max(errors)

# Bone geometry stays rigid; cloth and the glove have explicit local deformation domains.
body.vertex_groups.clear()
groups = {n: body.vertex_groups.new(name=n) for n in order + ['Jaw']}


def assign(i, weights):
    total = sum(weights.values()); assert total > 0
    for name, weight in weights.items():
        if weight > 1e-5: groups[name].add([int(i)], float(weight/total), 'REPLACE')


def blend(a, b, t):
    t = float(np.clip(t, 0, 1)); return {a: 1-t, b: t}


def spine_weights(z):
    names = ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head']
    heights = [1.08, 1.17, 1.30, 1.43, 1.53, 1.59]
    j = int(np.clip(np.searchsorted(heights, z)-1, 0, len(names)-2))
    return blend(names[j], names[j+1], (z-heights[j])/(heights[j+1]-heights[j]))


def hand_weights(point, sd, forced=None):
    options = []
    for finger, poly in finger_lines[sd].items():
        if forced is not None and finger != forced: continue
        for segment, (a, b) in enumerate(zip(poly, poly[1:])):
            d = b-a; t = float(np.clip(np.dot(point-a, d)/np.dot(d,d), 0, 1))
            options.append((np.linalg.norm(point-a-t*d), finger, segment, t))
    _, finger, segment, t = min(options)
    names = chain(sd, finger)
    a, b = finger_lines[sd][finger][:2]
    depth_local = np.dot(point-a, unit(b-a))
    if depth_local < .006:
        return blend(f'B_{sd}_Hand', names[0], (depth_local+.006)/.012)
    if t > .78 and segment < 2:
        return blend(names[segment], names[segment+1], (t-.78)/.44)
    if t < .22 and segment > 0:
        return blend(names[segment-1], names[segment], .5+t/.44)
    return {names[segment]: 1}


rigid = {19: 'B_L_UpperArm', 40: 'B_R_UpperArm', 15: 'B_L_Forearm', 4: 'B_L_Calf',
         7: 'B_R_Thigh', 8: 'B_L_Thigh', 10: 'B_L_Thigh', 11: 'B_R_Thigh',
         14: 'B_R_Calf', 26: 'B_L_Thigh', 27: 'B_R_Thigh', 3: 'B_R_Calf',
         89: 'B_L_Hand', 90: 'B_L_Hand', 91: 'B_L_Hand',
         2000: 'B_Head', 2001: 'Jaw', 2002: 'B_Head', 2003: 'Jaw'}
for pid in sorted(set(piece)):
    vertices = np.where(piece == pid)[0]; centre = co[vertices].mean(0)
    if pid in rigid:
        groups[rigid[pid]].add(vertices.tolist(), 1, 'REPLACE'); continue
    if pid not in [0, 1, 5, 6, 9] and pid not in left_parts.values():
        if centre[2] < .12:
            name = 'B_L_Foot'
        elif centre[2] < 1.02:
            name = 'B_L_Thigh' if centre[0] > centre_x else 'B_R_Thigh'
        elif centre[2] < 1.14:
            name = 'B_Pelvis'
        else:
            name = max(spine_weights(float(centre[2])).items(), key=lambda a:a[1])[0]
        groups[name].add(vertices.tolist(), 1, 'REPLACE'); continue
    for i in vertices:
        x, y, z = co[i]
        if pid in left_parts.values(): weights = hand_weights(co[i], 'L')
        elif pid == 5: weights = hand_weights(co[i], 'R', right_owner.get(int(i)))
        elif pid == 1: weights = blend('B_R_Foot', 'B_R_Calf', (z-.10)/.09)
        elif pid == 9:
            el, wr = joints['B_R_Forearm'], joints['B_R_Hand']
            t = float(np.dot(co[i]-el, unit(wr-el)))
            weights = blend('B_R_UpperArm', 'B_R_Forearm', (t+.035)/.07)
        elif z < 1.08:
            side = 'L' if x > centre_x else 'R'
            weights = blend('B_Pelvis', f'B_{side}_Thigh', (1.04-z)/(.30 if pid==6 else .16))
        else: weights = spine_weights(float(z))
        assign(i, weights)

# Keep connectivity ownership with the weights so animation rebuilds cannot reassign a fingertip by distance.
gn = {g.index:g.name for g in body.vertex_groups}
(P/'work/right_hand_weights.json').write_text(json.dumps([
    {'co':co[i].tolist(),'digit':right_owner.get(int(i)),
     'weights':{gn[g.group]:g.weight for g in me.vertices[i].groups}}
    for i in np.where(piece==5)[0]],indent=2))
# Separate bare phalanges at the measured joints so bone never stretches like skin.
segments = []
for finger, pid in left_parts.items():
    poly = finger_lines['L'][finger]
    names = chain('L', finger)
    for segment in range(-1 if finger else 0, 3):
        bm = bmesh.new(); bm.from_mesh(me)
        piece_layer = bm.verts.layers.int['piece']
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[piece_layer] != pid], context='VERTS')
        for lower, joint in [(True, segment), (False, segment+1)]:
            if joint < 0 or joint > 2:
                continue
            normal = Vector(unit(poly[min(joint+1, 3)]-poly[max(joint-1, 0)]))
            point = Vector(poly[joint]) + normal*(.0002 if lower else -.0002)
            cut = bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                dist=1e-6, plane_co=point, plane_no=normal, clear_inner=lower, clear_outer=not lower)
            bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
        assert len(bm.faces) > 0, (finger, segment)
        deform = bm.verts.layers.deform.verify()
        bone = 'B_L_Hand' if segment < 0 else names[segment]
        for v in bm.verts:
            v[deform].clear(); v[deform][groups[bone].index] = 1
            v[piece_layer] = 3000+finger*10+segment+1
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        mesh = bpy.data.meshes.new(f'Phalanx_{finger}_{segment}'); bm.to_mesh(mesh); bm.free()
        ob = bpy.data.objects.new(mesh.name, mesh); bpy.context.collection.objects.link(ob)
        for g in body.vertex_groups: ob.vertex_groups.new(name=g.name)
        for m in me.materials: mesh.materials.append(m)
        segments.append(ob)
bm = bmesh.new(); bm.from_mesh(me)
piece_layer = bm.verts.layers.int['piece']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[piece_layer] in left_parts.values()], context='VERTS')
bm.to_mesh(me); bm.free()
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True)
for ob in segments: ob.select_set(True)
bpy.context.view_layer.objects.active = body; bpy.ops.object.join(); me = body.data
assert all(abs(sum(g.weight for g in v.groups)-1) < 1e-4 for v in me.vertices)
assert all(len(v.groups) == 1 for v in me.vertices if me.attributes['piece'].data[v.index].value >= 3000)
body.parent = rig
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
scene = bpy.context.scene
scene['rig_offsets'] = json.dumps({n: {'q': list(swings[n]), 'R_src': source[n]['rot']} for n in order})
(P / 'work/joints_final.json').write_text(json.dumps({'joints': {n:v.tolist() for n,v in joints.items()},
    'right_elbow_inference': 'Mirrored exposed left elbow; the long right glove covers the joint.'}, indent=2))
(P / 'work/finger_joints.json').write_text(json.dumps({s: {str(f):p.tolist() for f,p in fs.items()}
    for s,fs in finger_lines.items()}, indent=2))
(P / 'work/rig_gate.json').write_text(json.dumps({'frame_error_degrees': max(min(x,360-x)for x in errors),
    'bones': len(ad.bones), 'vertices': len(me.vertices), 'all_weights_normalized': True,
    'bare_finger_rigid_segmentation': '19 capped pieces, one rigid influence each'}, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/rig_preview.blend'))
print('RIG FIT', len(ad.bones), 'bones; five fitted fingers per hand; bare phalanges rigid')
