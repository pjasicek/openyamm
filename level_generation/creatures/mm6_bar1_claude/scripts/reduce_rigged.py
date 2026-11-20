"""Triangle budget AFTER the weights (TEST_DRIVE.md: reducing before the Meshy weight transfer moved vertices up to
23 mm, mismatched weights and pushed the attack's arm stretch from 4.3x to 9.7x). Collapse decimation interpolates
vertex groups, so the finished weights survive. Per shell (piece) targets; on the skin the head (Head/Neck weight
> 0.3) and the hands (hand/finger weight > 0.3) are protected. Shells are separated, reduced and joined back with
the armature modifier. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
TARGET = {0: 4300, 1: 800, 2: 700, 3: 480, 4: 480, 5: 450, 6: 300, 7: 160, 8: 170, 9: 170, 10: 120, 12: 120}
before = sum(len(p.vertices) - 2 for p in me.polygons)
names = [g.name for g in body.vertex_groups]
prot = body.vertex_groups.new(name='_protect')
keys = [i for i, n in enumerate(names) if n in ('B_Head', 'B_Neck') or 'Hand' in n or 'Finger' in n]
for v in me.vertices:
    w = sum(e.weight for e in v.groups if e.group in keys)
    if w > 0.3:
        prot.add([v.index], 1.0, 'REPLACE')
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
parts = {}
for p, tgt in TARGET.items():
    for v in me.vertices:
        v.select = bool(pv[v.index] == p)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    me = body.data
    pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
    new = [o for o in bpy.context.selected_objects if o is not body]
    parts[p] = new[-1]
    for o in bpy.data.objects:
        o.select_set(o == body)
report = {}
for p, o in parts.items():
    tris = sum(len(f.vertices) - 2 for f in o.data.polygons)
    if tris > TARGET[p]:
        m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = TARGET[p] / tris
        m.vertex_group = '_protect'; m.invert_vertex_group = True
        bpy.context.view_layer.objects.active = o
        for x in bpy.data.objects:
            x.select_set(x == o)
        bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
        bpy.ops.object.modifier_apply(modifier='dec')
    report[p] = (tris, sum(len(f.vertices) - 2 for f in o.data.polygons))
for x in bpy.data.objects:
    x.select_set(x is body or x in parts.values())
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.vertex_groups.remove(body.vertex_groups['_protect'])
print('REDUCE', {p: f'{a}->{b}' for p, (a, b) in report.items()}, 'total', before, '->', sum(len(f.vertices) - 2 for f in body.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
