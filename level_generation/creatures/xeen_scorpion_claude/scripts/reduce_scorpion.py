"""LOD0 reduction after rigging (weights are rigid per piece, so they survive): edit-mode collapse decimation per
piece class (quadruped playbook: vertex-group Decimate barely reduces), then triangulation. Chelicerae 0.40, legs 0.45, body + tail
0.50, pedipalps 0.55, eyes 0.60. Saves work/reduced_v1.blend; renders review/reduced_*.png."""
import bpy, os, sys, json, bmesh
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
m = bpy.data.objects['Scorpion']
CLASSES = [(0.40, [11, 12, 13, 16]),      # chelicerae
           (0.45, [3, 4, 5, 6, 7, 8, 9, 10]),  # walking legs (thin tubes)
           (0.50, [0]),                    # body and tail
           (0.55, [1, 2]),                 # pedipalps and claws
           (0.60, [14, 15])]               # eyes
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
for view, (loc, tgt, s) in {'quarter': ((-2.6, -3.0, 1.9), (0, 0, 0.3), 1.8), 'front': ((0, -4, 0.42), (0, 0, 0.42), 1.8),
                            'head': ((-1.2, -3.0, 1.2), (0, -0.55, 0.15), 0.6), 'claw': ((1.5, -3, 1.2), (0.4, -0.65, 0.1), 0.5),
                            'tail': ((-3, 0.2, 1.0), (0, 0.4, 0.6), 0.8)}.items():
    C.render(loc, tgt, s, os.path.join(HERE, 'review', f'reduced_{view}.png'), res=(600, 600), floor=False)
