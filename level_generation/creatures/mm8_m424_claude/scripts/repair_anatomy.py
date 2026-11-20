"""Restore the missing ring fingers and pointed ears on the selected Smart Topology revision."""
from pathlib import Path
import json
import sys
import bpy
import bmesh
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import common

PROJECT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(PROJECT / 'work/st_v1_parts.blend'))
measurements = json.loads((PROJECT / 'work/hand_components.json').read_text())
report = {}

for name in ('P03', 'P04'):
    hand = bpy.data.objects[name]
    info = measurements[name]
    wrist = np.array(info['wrist'])
    direction = np.array(info['direction'])
    across = np.array(info['thumb_axis'])
    coords = np.array([tuple(v.co) for v in hand.data.vertices])
    forward = (coords - wrist) @ direction
    width = (coords - wrist) @ across
    components = next(r['components'] for r in info['rows'] if r['cut'] == .125)
    assert len(components) == 3, 'This repair belongs only to the measured three-finger return'
    centers = sorted(c['mean_w'] for c in components)
    middle = centers[1]

    # The new ring finger copies this hand's middle finger; the original palm and thumb stay in place.
    source = hand.data.copy()
    bm = bmesh.new()
    bm.from_mesh(source)
    bm.verts.ensure_lookup_table()
    kept = (forward > .088) & (width > (centers[0] + middle) / 2) & (width < (middle + centers[2]) / 2)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not kept[v.index]], context='VERTS')
    assert len(bm.faces) > 100
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary])
    for v in bm.verts:
        c = np.array(v.co)
        q = float((c - wrist) @ direction)
        w = float((c - wrist) @ across)
        new_w = middle - .014 + (w - middle) * .67
        new_q = .092 + (q - .092) * .94
        v.co = c + across * (new_w - w) + direction * (new_q - q)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(source)
    bm.free()
    added = bpy.data.objects.new(name + '_ring_finger', source)
    bpy.context.scene.collection.objects.link(added)

    # Make four narrow fingers fit the existing knuckle width, blending each adjustment into the palm.
    destinations = (centers[0] - .002, middle + .010, centers[2] + .001)
    for i, v in enumerate(hand.data.vertices):
        if forward[i] <= .088 or width[i] > .055:
            continue
        which = int(np.argmin(np.abs(np.array(centers) - width[i])))
        new_w = destinations[which] + (width[i] - centers[which]) * .70
        blend = float(np.clip((forward[i] - .088) / .025, 0, 1))
        blend = blend * blend * (3 - 2 * blend)
        v.co = coords[i] + across * ((new_w - width[i]) * blend)
    bm = bmesh.new()
    bm.from_mesh(hand.data)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(hand.data)
    bm.free()
    for obj in bpy.data.objects:
        obj.select_set(obj in (hand, added))
    bpy.context.view_layer.objects.active = hand
    bpy.ops.object.join()
    remesh = hand.modifiers.new('Join_repaired_finger', 'REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = .0012
    remesh.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth = hand.modifiers.new('Surface_cleanup', 'SMOOTH')
    smooth.factor = .30
    smooth.iterations = 2
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    reduce = hand.modifiers.new('Hand_budget', 'DECIMATE')
    reduce.ratio = .22
    bpy.ops.object.modifier_apply(modifier=reduce.name)
    smooth = hand.modifiers.new('Blend_source_facets', 'SMOOTH')
    smooth.factor = .5
    smooth.iterations = 6
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    for face in hand.data.polygons:
        face.use_smooth = True
    coords = np.array([tuple(v.co) for v in hand.data.vertices])
    forward = (coords - wrist) @ direction
    ids = set(np.where(forward > .13)[0].tolist())
    adjacency = {i: [] for i in ids}
    for edge in hand.data.edges:
        a, b = edge.vertices
        if a in ids and b in ids:
            adjacency[a].append(b)
            adjacency[b].append(a)
    fingers = []
    while ids:
        stack = [ids.pop()]
        component = []
        while stack:
            v = stack.pop()
            component.append(v)
            for n in adjacency[v]:
                if n in ids:
                    ids.remove(n)
                    stack.append(n)
        if len(component) > 5:
            fingers.append(component)
    assert len(fingers) == 4, (name, 'Long fingers must remain separate', len(fingers))
    report[name] = {'long_fingers': len(fingers), 'thumb': 'preserved from source',
                    'vertices': len(hand.data.vertices), 'triangles': len(hand.data.polygons)}
    print('FINGER_REPAIR', name, report[name])

body = bpy.data.objects['P00']
ear_changes = []
for side in (-1, 1):
    selected = [v for v in body.data.vertices
                if v.co.x * side > .058 and .012 < v.co.y < .055 and 1.56 < v.co.z < 1.615]
    maximum = max(v.co.x * side for v in selected)
    changed = 0
    for v in selected:
        outer = float(np.clip((v.co.x * side - .058) / (maximum - .058), 0, 1))
        upper = float(np.exp(-((v.co.z - 1.590) / .012) ** 2))
        depth = float(np.clip(min(v.co.y - .012, .055 - v.co.y) / .012, 0, 1))
        amount = outer * upper * depth
        v.co.x += side * .012 * amount
        v.co.z += .022 * amount
        v.co.y += .003 * amount
        changed += amount > 0
    ear_changes.append({'side': side, 'changed_vertices': changed})
assert all(x['changed_vertices'] > 5 for x in ear_changes)
report['ears'] = ear_changes
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT / 'work/anatomy_v2_parts.blend'))
(PROJECT / 'work/anatomy_v2_report.json').write_text(json.dumps(report, indent=2) + '\n')
common.workbench_clay(bpy.context.scene)
common.render_views(str(PROJECT / 'review/anatomy_v2_head'), 1.565, .32,
                    views=('front', 'left', 'three_quarter'), resolution=(600, 600))
for side, x in [('left', .48), ('right', -.48)]:
    common.render_views(str(PROJECT / ('review/anatomy_v2_hand_' + side)), .95, .29,
                        views=('front', 'back'), resolution=(600, 600), target=(x, 0))
