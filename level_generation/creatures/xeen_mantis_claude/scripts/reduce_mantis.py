"""LOD0 reduction after rigging (weights are rigid per piece, so they survive): edit-mode collapse decimation per
piece class (quadruped playbook: vertex-group Decimate barely reduces), then triangulation. Beads and antenna knobs
0.30, ball joints 0.45, feet 0.50, everything else 0.60. Saves work/reduced_v1.blend; renders review/reduced_*.png."""
import bpy, os, sys, json, bmesh
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
m = bpy.data.objects['Mantis']
CLASSES = [(0.30, [39, 40, 43, 44, 45, 46, 47, 49, 50, 51, 54, 55]),
           (0.45, [31, 33, 34, 35, 27, 29, 30, 32, 38, 42, 52, 53, 48]),
           (0.50, [2, 3, 4, 5])]
done = {p for _, ps in CLASSES for p in ps}
rest = [i for i in range(56) if i not in done]
CLASSES.append((0.60, rest))
t0 = sum(len(p.vertices) - 2 for p in m.data.polygons)
for o in bpy.data.objects: o.select_set(o == m)
bpy.context.view_layer.objects.active = m
for ratio, pieces in CLASSES:
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(m.data)
    lay = bm.faces.layers.int.get('piece')
    for f in bm.faces: f.select_set(False)
    for f in bm.faces:
        if f[lay] in pieces: f.select_set(True)
    bm.select_flush_mode(); bmesh.update_edit_mesh(m.data)
    bpy.ops.mesh.decimate(ratio=ratio)
    bpy.ops.object.mode_set(mode='OBJECT')
tri = m.modifiers.new('tri', 'TRIANGULATE'); tri.quad_method = 'SHORTEST_DIAGONAL'
bpy.ops.object.modifier_move_to_index(modifier='tri', index=0); bpy.ops.object.modifier_apply(modifier='tri')
t1 = len(m.data.polygons)
per = {}
att = m.data.attributes['piece']
for p in m.data.polygons:
    per[att.data[p.index].value] = per.get(att.data[p.index].value, 0) + 1
print('REDUCED', t0, '->', t1, 'pieces', len(per), 'unweighted', sum(1 for v in m.data.vertices if not v.groups))
print('PER_PIECE', sorted(per.items()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'reduced_v1.blend'))
for view, (loc, tgt, s) in {'quarter': ((-2.6, -3.0, 1.6), (0, 0, 0.5), 1.3), 'front': ((0, -4, 0.55), (0, 0, 0.55), 1.3),
                            'head': ((-1.2, -3.0, 1.2), (0, -0.25, 0.8), 0.5), 'foot': ((-1.5, -3, 0.8), (-0.35, -0.3, 0.05), 0.45)}.items():
    C.render(loc, tgt, s, os.path.join(HERE, 'review', f'reduced_{view}.png'), res=(600, 600), floor=False)
