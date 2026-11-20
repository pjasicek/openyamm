"""Teeth and spikes over every frame of every clip (work/rebuild.blend): their vertices that stand outside the body
in the rest pose must stay outside it (inside by ray parity, depth = distance to the body surface), so no tooth
enters the opposite jaw and no spike sinks into the neck when it bends. Writes work/parts_gate.json.
Usage: blender -b -P parts_gate.py"""
import json, os, bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_BLEND', 'rebuild.blend')))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; obj = bpy.data.objects['Rebuilt']
part = np.array([a.value for a in obj.data.attributes['part'].data])


def state():
    b = bmesh.new(); b.from_object(obj, bpy.context.evaluated_depsgraph_get()); b.verts.ensure_lookup_table()
    b.faces.ensure_lookup_table()
    co = np.array([v.co[:] for v in b.verts])
    body = [f for f in b.faces if part[f.index] == 0]  # the thin mouth interior defeats the sign test
    tree = BVHTree.FromPolygons([v.co.copy() for v in b.verts], [[v.index for v in f.verts] for f in body])
    b.free(); return co, tree


DIRS = [Vector(d).normalized() for d in ((1, .1, .2), (-1, .2, .1), (.1, 1, .3), (.2, -1, .1), (.1, .2, 1), (.2, .1, -1))]


def inside(tree, p):
    """ray parity voted over six directions (the nearest-face sign misfires next to folds and thin parts)"""
    odd = 0
    for d in DIRS:
        o, hits = Vector(p), 0
        while hits < 50:
            loc, _, _, dist = tree.ray_cast(o, d)
            if loc is None:
                break
            hits += 1; o = loc + d * 1e-6
        odd += hits % 2
    return odd >= 4


def signed(co, tree, ids):
    """distance to the body surface, negative when the point is inside the body"""
    out = []
    for i in ids:
        d = tree.find_nearest(co[i])[3]
        out.append(-d if inside(tree, co[i]) else d)
    return np.array(out)


rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
co, tree = state()
verts = {k: sorted({v for p in obj.data.polygons if part[p.index] == k for v in p.vertices}) for k in (4, 5)}
rest = {k: signed(co, tree, ids) for k, ids in verts.items()}
test = {k: [i for i, s in zip(verts[k], rest[k]) if s > .0005] for k in verts}
piece = obj.data.attributes['piece'].data if 'piece' in obj.data.attributes else None
vpiece = {}
if piece is not None:
    for p in obj.data.polygons:
        for v in p.vertices:
            vpiece[v] = piece[p.index].value
per_piece = {}
report = {}
for act in bpy.data.actions:
    rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); worst = {4: (0, None), 5: (0, None)}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); co, tree = state()
        for k in (4, 5):
            s = signed(co, tree, test[k]); m = float(s.min())
            for i, x in zip(test[k], s):
                if x < -.0003 and i in vpiece:
                    per_piece[vpiece[i]] = min(per_piece.get(vpiece[i], 0), float(x))
            if m < worst[k][0]:
                worst[k] = (m, f)
    report[act.name] = {'spike_min_mm': round(worst[4][0] * 1000, 2), 'spike_frame': worst[4][1],
                        'tooth_min_mm': round(worst[5][0] * 1000, 2), 'tooth_frame': worst[5][1]}
    print('GATE', act.name, report[act.name], flush=True)
report['per_piece_mm'] = {str(k): round(v * 1000, 2) for k, v in sorted(per_piece.items())}
print('PIECES', report['per_piece_mm'])
json.dump(report, open(os.path.join(HERE, 'work', os.environ.get('REA_GATE_OUT', 'parts_gate.json')), 'w'), indent=1)
