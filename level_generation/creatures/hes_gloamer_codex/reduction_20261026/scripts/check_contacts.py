"""Repeat the existing disjoint-skin contact checks on assembled old/new runtime elder GLBs at 60 Hz."""
import bpy
import json
import os
from pathlib import Path
import sys
import numpy as np
from mathutils.bvhtree import BVHTree

R = Path(__file__).resolve().parents[1]
P = R.parent
report = {}
for label, path in [('before', R / 'before/viewer/gloamer_c.glb'), ('reduced', P / 'review/viewer/gloamer_c.glb')]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=str(path))
    rig = next(o for o in scene.objects if o.type == 'ARMATURE')
    body = bpy.data.objects['Gloamer']
    sac = next(o for o in scene.objects if o.type == 'MESH' and o != body)
    rig.animation_data.action = None
    for bone in rig.pose.bones: bone.matrix_basis.identity()
    bpy.context.view_layer.update()
    mesh = body.data
    co = np.array([v.co[:] for v in mesh.vertices])
    world = np.array(body.matrix_world)
    rest = co @ world[:3, :3].T + world[:3, 3]
    faces = np.array([f.vertices[:] for f in mesh.polygons])
    edges = np.array([e.vertices[:] for e in mesh.edges])
    restlen = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
    assert (restlen > 1e-8).all()
    # UV/normal splits count as one surface for component labels, without changing runtime vertices or weights.
    _, welded = np.unique(np.round(co, 6), axis=0, return_inverse=True)
    parent = list(range(int(welded.max()) + 1))
    def root(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for tri in welded[faces]:
        for a, b in zip(tri, np.roll(tri, 1)): parent[root(a)] = root(b)
    piece = np.array([root(t[0]) for t in welded[faces]])
    skin = faces[piece == np.bincount(piece).argmax()]
    names = [g.name for g in body.vertex_groups]
    weights = np.zeros((len(co), len(names)))
    for v in mesh.vertices:
        for g in v.groups: weights[v.index, g.group] = g.weight
    def weight(parts):
        return weights[:, [i for i, n in enumerate(names) if any(s in n for s in parts)]].sum(1)
    arms = weight(['UpperArm', 'Forearm', 'Hand', 'Finger'])
    hands = weight(['Hand', 'Finger'])
    legs = weight(['Thigh', 'Calf', 'Foot', 'Toe'])
    trunk = weight(['Pelvis', 'Spine', 'Neck', 'Head'])
    regions = {'arms': skin[np.all(arms[skin] > .9, axis=1)],
               'legs': skin[np.all(legs[skin] > .9, axis=1)],
               'torso': skin[np.all((trunk[skin] > .9) & (rest[skin, 2] > 1.03), axis=1)],
               'left': skin[np.all((arms[skin] > .9) & (rest[skin, 0] > 0), axis=1)],
               'right': skin[np.all((arms[skin] > .9) & (rest[skin, 0] < 0), axis=1)]}
    assert all(len(f) for f in regions.values())
    arm_edges = np.all(arms[edges] > .3, axis=1)
    hand_edges = np.all(hands[edges] > .3, axis=1)
    def posed(obj):
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        m = evaluated.to_mesh()
        a = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', a)
        evaluated.to_mesh_clear(); matrix = np.array(evaluated.matrix_world)
        return a.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
    result = {}
    for action in bpy.data.actions:
        rig.animation_data.action = action
        if action.slots: rig.animation_data.action_slot = action.slots[0]
        row = {'arm_leg': 0, 'arm_torso': 0, 'arm_arm': 0, 'sac_arm': 0,
               'arm_stretch_p99': 0, 'hand_stretch_max': 0, 'samples': 0}
        for frame in np.arange(action.frame_range[0], action.frame_range[1] + .0001, .5):
            scene.frame_set(int(frame), subframe=float(frame % 1))
            v = posed(body); points = v.tolist(); assert np.isfinite(v).all()
            trees = {k: BVHTree.FromPolygons(points, f.tolist(), all_triangles=True) for k, f in regions.items()}
            sac_tree = BVHTree.FromPolygons(posed(sac).tolist(), [tuple(f.vertices) for f in sac.data.polygons], all_triangles=True)
            counts = {'arm_leg': len(trees['arms'].overlap(trees['legs'])),
                      'arm_torso': len(trees['arms'].overlap(trees['torso'])),
                      'arm_arm': len(trees['left'].overlap(trees['right'])),
                      'sac_arm': len(trees['arms'].overlap(sac_tree))}
            stretch = np.linalg.norm(v[edges[:, 0]] - v[edges[:, 1]], axis=1) / restlen
            counts['arm_stretch_p99'] = float(np.percentile(stretch[arm_edges], 99))
            counts['hand_stretch_max'] = float(stretch[hand_edges].max())
            for k, value in counts.items(): row[k] = max(row[k], value)
            row['samples'] += 1
        result[action.name] = row
        print(label, action.name, row, flush=True)
    assert len(result) == 9
    report[label] = result
for clip, row in report['reduced'].items():
    for key in ('arm_leg', 'arm_torso', 'arm_arm', 'sac_arm'):
        assert row[key] == 0, (clip, key, row[key])
    for key in ('arm_stretch_p99', 'hand_stretch_max'):
        assert row[key] <= report['before'][clip][key] * 1.1, (clip, key, row[key])
(R / 'review/contacts.json').write_text(json.dumps({'pass': True, 'sample_hz': 60, 'clips': report}, indent=2) + '\n')
sys.stdout.flush();sys.stderr.flush();os._exit(0)
